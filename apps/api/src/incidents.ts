import {
  Body,
  Controller,
  Get,
  Post,
  Param,
  Query,
  Req,
  UseGuards,
  ParseUUIDPipe,
  Injectable,
  Inject,
  NotFoundException,
  HttpCode,
} from '@nestjs/common';
import { ApiBody, ApiCookieAuth, ApiPropertyOptional, ApiTags } from '@nestjs/swagger';
import { IsDateString, IsEnum, IsOptional, IsUUID } from 'class-validator';
import type { IncidentActionV1 } from '@radar/contracts';
import { Database } from './database.js';
import { IncidentStatus, SourceMode } from './generated/prisma/enums.js';
import type { Incident } from './generated/prisma/client.js';
import { HumanGuard } from './identity.js';
import type { HumanRequest, Principal } from './identity.js';
import { ListDto } from './dto.js';
import { pageArguments, pageResult } from './pagination.js';
import { CLOCK, ContractPipe, contentHash, fail } from './event-support.js';
import type { Clock } from './event-support.js';

export class IncidentListDto extends ListDto {
  @ApiPropertyOptional({ enum: IncidentStatus })
  @IsOptional()
  @IsEnum(IncidentStatus)
  status?: IncidentStatus;
  @ApiPropertyOptional({ enum: SourceMode })
  @IsOptional()
  @IsEnum(SourceMode)
  mode?: SourceMode;
  @ApiPropertyOptional({ format: 'uuid' })
  @IsOptional()
  @IsUUID()
  cameraId?: string;
  @ApiPropertyOptional({ format: 'date-time' })
  @IsOptional()
  @IsDateString({ strict: true })
  from?: string;
  @ApiPropertyOptional({ format: 'date-time' })
  @IsOptional()
  @IsDateString({ strict: true })
  to?: string;
}

export function publicIncident(incident: Incident) {
  const { episodeHash: ignored, sourceOffsetMs, ...result } = incident;
  void ignored;
  return { ...result, sourceOffsetMs: sourceOffsetMs === null ? null : Number(sourceOffsetMs) };
}

@Injectable()
export class IncidentService {
  constructor(
    private readonly database: Database,
    @Inject(CLOCK) private readonly clock: Clock,
  ) {}
  async act(principal: Principal, incidentId: string, body: IncidentActionV1) {
    const tenantId = principal.tenantId;
    const hash = contentHash({ incidentId, ...body });
    return this.database.$transaction(
      async (tx) => {
        if (
          !(await tx.incident.findUnique({ where: { tenantId_id: { tenantId, id: incidentId } } }))
        )
          throw new NotFoundException('Incidente não encontrado.');
        // Mesmo actionId é serializado até em requisições a incidentes diferentes.
        await tx.$executeRaw`SELECT pg_advisory_xact_lock(hashtext(${tenantId}), hashtext(${body.actionId}))`;
        const previous = await tx.incidentAction.findUnique({
          where: { tenantId_actionId: { tenantId, actionId: body.actionId } },
        });
        if (previous) {
          if (previous.payloadHash !== hash) fail(409, 'ACTION_ID_CONFLICT');
          return previous.result;
        }
        await tx.$queryRaw`SELECT "id" FROM "Incident" WHERE "tenantId"=${tenantId}::uuid AND "id"=${incidentId}::uuid FOR UPDATE`;
        const incident = await tx.incident.findUniqueOrThrow({
          where: { tenantId_id: { tenantId, id: incidentId } },
        });
        if (incident.version !== body.expectedVersion) fail(409, 'VERSION_CONFLICT');
        const final = incident.status === 'RESOLVED' || incident.status === 'DISMISSED';
        if (final && body.action !== 'ADD_NOTE') fail(409, 'INVALID_TRANSITION');
        let { status, review, outcome, dismissReason } = incident;
        switch (body.action) {
          case 'RECOGNIZE':
            if (status !== 'OPEN') fail(409, 'INVALID_TRANSITION');
            status = 'ACKNOWLEDGED';
            break;
          case 'START_RESPONSE':
            if (status !== 'ACKNOWLEDGED') fail(409, 'INVALID_TRANSITION');
            status = 'IN_PROGRESS';
            break;
          case 'SET_REVIEW':
            review = body.review;
            break;
          case 'RESOLVE':
            if (status !== 'ACKNOWLEDGED' && status !== 'IN_PROGRESS')
              fail(409, 'INVALID_TRANSITION');
            status = 'RESOLVED';
            outcome = body.outcome;
            review = body.review;
            break;
          case 'DISMISS':
            status = 'DISMISSED';
            dismissReason = body.reason;
            review =
              body.reason === 'FALSE_DETECTION'
                ? 'FALSE_POSITIVE'
                : review === 'UNREVIEWED'
                  ? 'INCONCLUSIVE'
                  : review;
            break;
          case 'ADD_NOTE':
            break;
        }
        const updatedAt = this.clock.now();
        const updated = await tx.incident.update({
          where: { tenantId_id: { tenantId, id: incidentId } },
          data: { status, review, outcome, dismissReason, version: { increment: 1 }, updatedAt },
        });
        const result = {
          incidentId,
          actionId: body.actionId,
          status,
          review,
          outcome,
          dismissReason,
          version: updated.version,
          updatedAt: updatedAt.toISOString(),
        };
        const action = await tx.incidentAction.create({
          data: {
            tenantId,
            incidentId,
            actorId: principal.id,
            actionId: body.actionId,
            action: body.action,
            payloadHash: hash,
            payload: body,
            result,
            createdAt: updatedAt,
          },
        });
        await tx.auditEntry.create({
          data: {
            tenantId,
            actorId: principal.id,
            incidentId,
            incidentActionId: action.id,
            objectId: action.id,
            action: `INCIDENT_${body.action}`,
            resultCode: 'COMMITTED',
            fromVersion: incident.version,
            toVersion: updated.version,
            createdAt: updatedAt,
          },
        });
        return result;
      },
      { maxWait: 10000, timeout: 10000 },
    );
  }
}

@ApiTags('incidents')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard)
@Controller('incidents')
export class IncidentsController {
  constructor(
    private readonly database: Database,
    private readonly service: IncidentService,
  ) {}
  @Get()
  async list(@Req() request: HumanRequest, @Query() query: IncidentListDto) {
    if (query.from && query.to && Date.parse(query.from) > Date.parse(query.to))
      fail(400, 'INVALID_INTERVAL');
    const args = pageArguments(query);
    const rows = await this.database.incident.findMany({
      ...args,
      where: {
        ...args.where,
        tenantId: request.principal.tenantId,
        status: query.status,
        mode: query.mode,
        cameraId: query.cameraId,
        occurredAt: {
          gte: query.from ? new Date(query.from) : undefined,
          lte: query.to ? new Date(query.to) : undefined,
        },
      },
      orderBy: [{ createdAt: 'asc' }, { id: 'asc' }],
    });
    const page = pageResult(rows, query.limit);
    return { ...page, items: page.items.map(publicIncident) };
  }
  @Get(':id')
  async get(@Req() request: HumanRequest, @Param('id', ParseUUIDPipe) id: string) {
    const row = await this.database.incident.findUnique({
      where: { tenantId_id: { tenantId: request.principal.tenantId, id } },
    });
    if (!row) throw new NotFoundException('Incidente não encontrado.');
    return publicIncident(row);
  }
  @Post(':id/actions')
  @HttpCode(200)
  @ApiBody({ schema: { $ref: '#/components/schemas/IncidentActionV1' } })
  act(
    @Req() request: HumanRequest,
    @Param('id', ParseUUIDPipe) id: string,
    @Body(new ContractPipe('incident-action-v1')) body: IncidentActionV1,
  ) {
    return this.service.act(request.principal, id, body);
  }
}

export class AuditListDto extends ListDto {
  @ApiPropertyOptional({ format: 'uuid' })
  @IsOptional()
  @IsUUID()
  incidentId?: string;
}
@ApiTags('audit')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard)
@Controller('audit')
export class AuditController {
  constructor(private readonly database: Database) {}
  @Get()
  async list(@Req() request: HumanRequest, @Query() query: AuditListDto) {
    if (
      query.incidentId &&
      !(await this.database.incident.findUnique({
        where: { tenantId_id: { tenantId: request.principal.tenantId, id: query.incidentId } },
      }))
    )
      throw new NotFoundException('Incidente não encontrado.');
    const args = pageArguments(query);
    return pageResult(
      await this.database.auditEntry.findMany({
        ...args,
        where: {
          ...args.where,
          tenantId: request.principal.tenantId,
          incidentId: query.incidentId,
        },
        include: {
          incidentAction: {
            select: { actionId: true, actorId: true, action: true, payload: true, result: true },
          },
        },
        orderBy: [{ createdAt: 'asc' }, { id: 'asc' }],
      }),
      query.limit,
    );
  }
}
