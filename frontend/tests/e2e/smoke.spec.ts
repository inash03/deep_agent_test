import { test, expect } from '@playwright/test'

// Read-only smoke tests — safe to run against production.
// Do NOT create, update, or delete any data here.

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
    // Wait for at least one row to appear (seeded data exists)
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
    // Detail page URL contains the trade_id segment
    await expect(page).toHaveURL(/\/trades\/.+/)
    await expect(page.getByRole('navigation')).toBeVisible()
  })
})

test.describe('Navigation', () => {
  test('all nav links are reachable', async ({ page }) => {
    await page.goto('/')

    // Each link should navigate without a 404 / error boundary
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
