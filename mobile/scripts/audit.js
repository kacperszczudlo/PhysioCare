const { execSync } = require('node:child_process')

// Known upstream zero-day advisories without an upstream fix available yet.
// Both are build/bundler tooling dependencies (Metro/Expo CLI), not runtime client code:
// - GHSA-vfj7-8cjw-p6xm: braces <= 3.0.3 (stack-exhaustion DoS in AST parser)
// - GHSA-86w9-cpqp-85rv: node-forge <= 1.4.0 (RSA PKCS#1 v1.5 verification element count)
const IGNORED_ADVISORY_URLS = new Set([
  'https://github.com/advisories/GHSA-vfj7-8cjw-p6xm',
  'https://github.com/advisories/GHSA-86w9-cpqp-85rv',
])

let jsonOutput = ''
try {
  jsonOutput = execSync('npm audit --json', {
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe'],
  })
} catch (error) {
  jsonOutput = error.stdout?.toString() || ''
}

if (!jsonOutput) {
  console.log('No npm audit output received.')
  process.exit(0)
}

const audit = JSON.parse(jsonOutput)
const unhandledIssues = []

for (const [pkg, info] of Object.entries(audit.vulnerabilities || {})) {
  if (info.severity !== 'high' && info.severity !== 'critical') {
    continue
  }

  const queue = [...info.via]
  const visited = new Set()
  let hasUnhandledRoot = false
  const sourceUrls = []

  while (queue.length > 0) {
    const item = queue.shift()
    if (typeof item === 'string') {
      if (!visited.has(item)) {
        visited.add(item)
        const parentVuln = audit.vulnerabilities[item]
        if (parentVuln) {
          queue.push(...parentVuln.via)
        }
      }
    } else if (item && typeof item === 'object') {
      sourceUrls.push(item.url)
      if (!IGNORED_ADVISORY_URLS.has(item.url)) {
        hasUnhandledRoot = true
      }
    }
  }

  if (hasUnhandledRoot) {
    unhandledIssues.push({ package: pkg, severity: info.severity, sources: sourceUrls })
  }
}

if (unhandledIssues.length > 0) {
  console.error('Unhandled high/critical vulnerabilities found in mobile dependencies:')
  console.error(JSON.stringify(unhandledIssues, null, 2))
  process.exit(1)
}

console.log(
  'Mobile dependency audit passed: no unhandled high/critical vulnerabilities (known upstream unpatched Metro/Expo advisories suppressed).',
)
