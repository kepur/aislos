export default defineEventHandler((event) => {
  const origin = getRequestURL(event).origin
  setHeader(event, 'Content-Type', 'text/plain; charset=utf-8')
  return [
    'User-agent: *',
    'Allow: /',
    `Sitemap: ${origin}/sitemap.xml`,
    '',
  ].join('\n')
})
