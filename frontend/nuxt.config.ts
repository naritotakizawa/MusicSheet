export default defineNuxtConfig({
  devtools: { enabled: true },
  build: {
    transpile: ['vexflow'],
  },
  app: {
    head: {
      link: [
        {
          rel: 'stylesheet',
          href: 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
        },
      ],
    },
  },
})
