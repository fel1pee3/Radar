import { isEmail } from 'class-validator';
import type { PrismaClient } from './generated/prisma/client.js';
import { hashPassword, validatePassword } from './security.js';

export interface BootstrapInput {
  email: string;
  password: string;
  tenantSlug?: string;
  tenantName?: string;
  siteName?: string;
  timezone?: string;
}
export function validateEmail(value: string | undefined): string {
  const email = value?.trim().toLowerCase() ?? '';
  if (!isEmail(email) || email.length > 254) throw new Error('Configure um e-mail válido.');
  return email;
}

export async function seed(database: PrismaClient, input: BootstrapInput) {
  const email = validateEmail(input.email);
  validatePassword(input.password);
  const slug = input.tenantSlug ?? 'demo';
  const timezone = input.timezone ?? 'America/Sao_Paulo';
  if (!/^[a-z0-9][a-z0-9-]{0,79}$/.test(slug)) throw new Error('Slug do tenant inválido.');
  new Intl.DateTimeFormat('pt-BR', { timeZone: timezone });
  for (const name of [input.tenantName, input.siteName]) {
    if (name !== undefined && (!name.trim() || name.length > 120))
      throw new Error('Nome inválido.');
  }
  return database.$transaction(
    async (tx) => {
      await tx.$executeRaw`SELECT pg_advisory_xact_lock(hashtext('radar-bootstrap'))`;
      const tenant = await tx.tenant.upsert({
        where: { slug },
        create: { slug, name: input.tenantName ?? 'Bancada Radar' },
        update: {},
      });
      const existing = await tx.user.findUnique({ where: { email } });
      if (
        existing &&
        (existing.tenantId !== tenant.id || existing.role !== 'OWNER' || !existing.active)
      ) {
        throw new Error('E-mail já vinculado a outro escopo ou papel. Nenhum acesso foi alterado.');
      }
      if (
        !existing &&
        (await tx.user.findFirst({ where: { tenantId: tenant.id, role: 'OWNER' } }))
      ) {
        throw new Error(
          'O tenant já possui proprietário. O bootstrap não cria outro proprietário nem altera a conta existente.',
        );
      }
      const owner =
        existing ??
        (await tx.user.create({
          data: {
            tenantId: tenant.id,
            email,
            role: 'OWNER',
            passwordHash: await hashPassword(input.password),
          },
        }));
      const site = await tx.site.upsert({
        where: { tenantId_bootstrapKey: { tenantId: tenant.id, bootstrapKey: 'default' } },
        create: {
          tenantId: tenant.id,
          bootstrapKey: 'default',
          name: input.siteName ?? 'Local de demonstração',
          timezone,
        },
        update: {},
      });
      if (!existing)
        await tx.auditEntry.create({
          data: {
            tenantId: tenant.id,
            actorId: owner.id,
            action: 'OWNER_BOOTSTRAPPED',
            objectId: owner.id,
          },
        });
      return { tenantId: tenant.id, ownerId: owner.id, siteId: site.id, created: !existing };
    },
    { timeout: 10000 },
  );
}

export async function createOperator(
  database: PrismaClient,
  input: { email: string; password: string; tenantSlug?: string },
) {
  const email = validateEmail(input.email);
  validatePassword(input.password);
  return database.$transaction(
    async (tx) => {
      await tx.$executeRaw`SELECT pg_advisory_xact_lock(hashtext('radar-bootstrap'))`;
      const tenant = await tx.tenant.findUnique({ where: { slug: input.tenantSlug ?? 'demo' } });
      if (
        !tenant ||
        !(await tx.user.findFirst({ where: { tenantId: tenant.id, role: 'OWNER', active: true } }))
      )
        throw new Error('Crie o proprietário do tenant antes do operador.');
      const existing = await tx.user.findUnique({ where: { email } });
      if (existing && (existing.tenantId !== tenant.id || existing.role !== 'OPERATOR'))
        throw new Error('E-mail já vinculado a outro escopo ou papel.');
      const user =
        existing ??
        (await tx.user.create({
          data: {
            tenantId: tenant.id,
            email,
            role: 'OPERATOR',
            passwordHash: await hashPassword(input.password),
          },
        }));
      if (!existing)
        await tx.auditEntry.create({
          data: { tenantId: tenant.id, action: 'OPERATOR_CREATED', objectId: user.id },
        });
      return { id: user.id, tenantId: tenant.id, created: !existing };
    },
    { timeout: 10000 },
  );
}
