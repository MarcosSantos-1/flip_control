# Arquitetura sugerida (alto nível)

**Frontend**

* React + TypeScript + Next.js
* Tailwind CSS + shadcn/ui (componentes)
* Tema: ` claro` por padrão mas com botão para alterar `dark` com paleta `zinc` + `violet` + gradientes para highlights (usar classes do próprio tailwind como o "dark:")
* Charts: Recharts ou Chart.js (Next + dynamic import) ou do shadcn (sou leigo nessa parte, nunca fiz nada com Charts)

**Backend**

* **Opção recomendada (produtiva ):**
  * python
    PostgreSQL (Neon)

**Infra / Deploy**

* Frontend: Vercel
* Backend: Render / ou  Fly / Render (acho que vou de fly.io )
* DB: Neon (Postgres)
* CI: GitHub Actions

**O sistema deve ser elegante com inputs e componentes modernos e de alto nível, simplificando processos e aumentando a produtividade.**
