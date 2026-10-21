import { Catch, HttpException, Logger } from '@nestjs/common';
import type { ArgumentsHost, ExceptionFilter } from '@nestjs/common';
import type { Response } from 'express';

@Catch()
export class SafeExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger('HTTP');
  catch(error: unknown, host: ArgumentsHost): void {
    let status = 500;
    let code = 'INTERNAL_ERROR';
    let message = 'Não foi possível concluir a operação.';
    if (error instanceof HttpException) {
      status = error.getStatus();
      const payload = error.getResponse();
      code = `HTTP_${status}`;
      message = status === 400 ? 'Dados inválidos ou campos não permitidos.' : error.message;
      if (
        typeof payload === 'object' &&
        payload !== null &&
        'code' in payload &&
        typeof payload.code === 'string'
      ) {
        code = payload.code;
      }
    } else if (
      typeof error === 'object' &&
      error !== null &&
      'status' in error &&
      (error.status === 400 || error.status === 413)
    ) {
      status = error.status;
      code = status === 413 ? 'PAYLOAD_TOO_LARGE' : 'INVALID_JSON';
      message = status === 413 ? 'Corpo da requisição excede 64 KiB.' : 'JSON inválido.';
    } else if (typeof error === 'object' && error !== null && 'code' in error) {
      if (error.code === 'P2002') {
        status = 409;
        code = 'RESOURCE_CONFLICT';
        message = 'Registro já existente.';
      } else if (error.code === 'P2003') {
        status = 400;
        code = 'INVALID_REFERENCE';
        message = 'Referência inválida.';
      } else if (error.code === 'P2025') {
        status = 404;
        code = 'NOT_FOUND';
        message = 'Registro não encontrado.';
      } else {
        status = 503;
        code = 'DATABASE_UNAVAILABLE';
        message = 'Banco temporariamente indisponível.';
      }
    }
    // Somente códigos controlados; jamais mensagem/stack/contexto de bibliotecas.
    if (status >= 500) this.logger.error({ event: 'request_failed', code, status });
    host
      .switchToHttp()
      .getResponse<Response>()
      .status(status)
      .json({ statusCode: status, code, message });
  }
}
