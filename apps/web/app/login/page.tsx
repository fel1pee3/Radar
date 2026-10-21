'use client';
import { LoginForm } from '../../components/session';
export default function Login() {
  return (
    <main className="login-screen">
      <div className="login-intro">
        <p className="eyebrow">PERCEPÇÃO LOCAL. REVISÃO HUMANA.</p>
        <h2>
          O contexto faz
          <br />a diferença.
        </h2>
        <p>
          Uma suspeita explicável.
          <br />
          Uma resposta registrada.
        </p>
        <div className="radar-art" aria-hidden="true">
          <i />
          <i />
          <i />
          <b />
        </div>
        <span className="fine">MVP de demonstração · Sem garantia de assistência</span>
      </div>
      <LoginForm />
    </main>
  );
}
