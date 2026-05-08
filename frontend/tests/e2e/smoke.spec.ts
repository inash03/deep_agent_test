import { test, expect } from '@playwright/test'

// Read-only smoke tests; safe to run against production.
// Do NOT create, update, or delete any data here.

const username = process.env.APP_USERNAME
const password = process.env.APP_PASSWORD

test.beforeEach(async ({ page }) => {
  test.skip(!username || !password, 'APP_USERNAME and APP_PASSWORD are required for authenticated smoke tests.')

  await page.goto('/login')
  await page.getByLabel('Username').fill(username!)
  await page.getByLabel('Password').fill(password!)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/$/)
})

test.describe('Home', () => {
  test('page loads and shows app title', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/STP/)
    await expect(page.getByRole('navigation')).toBeVisible()
  })
})

test.describe('Trade List', () => {
  test('page loads and shows trade table', async ({ page }) => {
    await page.goto('/trades')
    await expect(page.locator('table tbody tr').first()).toBeVisible()
  })

  test('trade rows contain trade IDs', async ({ page }) => {
    await page.goto('/trades')
    await expect(page.locator('table tbody tr').first()).toContainText('TRD-')
  })
})

test.describe('Trade Detail', () => {
  test('clicking a trade row opens detail page', async ({ page }) => {
    await page.goto('/trades')
    const firstRow = page.locator('table tbody tr').first()
    await firstRow.click()
    await expect(page).toHaveURL(/\/trades\/.+/)
    await expect(page.getByRole('navigation')).toBeVisible()
  })
})

test.describe('Navigation', () => {
  test('all nav links are reachable', async ({ page }) => {
    await page.goto('/')

    const links: [string, RegExp][] = [
      ['Trades', /\/trades/],
      ['History', /\/history/],
      ['Rules', /\/rules/],
      ['Cost', /\/cost/],
      ['Settings', /\/settings/],
    ]

    for (const [label, pattern] of links) {
      const link = page.getByRole('link', { name: label }).first()
      if (await link.isVisible()) {
        await link.click()
        await expect(page).toHaveURL(pattern)
      }
    }
  })
})
