import { PartialType, ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Transform, Type } from 'class-transformer';
import {
  IsBoolean,
  IsEmail,
  IsEnum,
  IsInt,
  IsOptional,
  IsString,
  IsUUID,
  Length,
  Max,
  MaxLength,
  Min,
  MinLength,
  ValidateBy,
} from 'class-validator';
import { CameraType } from './generated/prisma/enums.js';

const Trim = () =>
  Transform(({ value }: { value: unknown }) => (typeof value === 'string' ? value.trim() : value));

export class LoginDto {
  @ApiProperty({ format: 'email', maxLength: 254 })
  @Trim()
  @IsEmail()
  @MaxLength(254)
  email!: string;

  @ApiProperty({ format: 'password', minLength: 1, maxLength: 128, writeOnly: true })
  @IsString()
  @MinLength(1)
  @MaxLength(128)
  password!: string;
}

export class SiteDto {
  @ApiProperty({ minLength: 1, maxLength: 120 })
  @Trim()
  @IsString()
  @Length(1, 120)
  name!: string;

  @ApiProperty({ example: 'America/Sao_Paulo' })
  @IsString()
  @MaxLength(80)
  @ValidateBy({
    name: 'timezone',
    validator: {
      validate(value: unknown) {
        try {
          if (typeof value !== 'string') return false;
          new Intl.DateTimeFormat('pt-BR', { timeZone: value });
          return true;
        } catch {
          return false;
        }
      },
    },
  })
  timezone!: string;
}
export class SitePatchDto extends PartialType(SiteDto, { skipNullProperties: false }) {}

export class CameraDto {
  @ApiProperty({ format: 'uuid' })
  @IsUUID()
  siteId!: string;

  @ApiProperty({ minLength: 1, maxLength: 120 })
  @Trim()
  @IsString()
  @Length(1, 120)
  name!: string;

  @ApiProperty({ enum: CameraType })
  @IsEnum(CameraType)
  type!: CameraType;

  @ApiPropertyOptional({ default: false })
  @IsOptional()
  @IsBoolean()
  expectedRunning?: boolean;
}
export class CameraPatchDto extends PartialType(CameraDto, { skipNullProperties: false }) {}

export class ListDto {
  @ApiPropertyOptional({ type: Number, default: 20, minimum: 1, maximum: 100 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit: number = 20;

  @ApiPropertyOptional({ maxLength: 1024 })
  @IsOptional()
  @IsString()
  @MaxLength(1024)
  cursor?: string;
}
