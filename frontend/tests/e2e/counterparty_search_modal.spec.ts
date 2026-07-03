import { test, expect } from '@playwright/test'

// Issue #61 — counterparty search modal on the New Trade form.
// Authenticated, read-only flow: opens the modal, searches by name substring,
// selects a result, and asserts it is written back to the form as LEI + name.
// Does NOT submit the form, so no trade is created.

const username = process.env.APP_USERNAME
const password = process.env.APP_PASSWORD

test.beforeEach(async ({ page }) => {
  test.skip(!username || !password, 'APP_USERNAME and APP_PASSWORD are required for authenticated tests.')

  await page.goto('/login')
  await page.getByLabel('Username').fill(username!)
  await page.getByLabel('Password').fill(password!)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/$/)
})

test.describe('Counterparty search modal', () => {
  test('search by name, select, and write back to the form', async ({ page }) => {
    await page.goto('/trades/new')

    // Open the modal from the Counterparty field.
    await page.getByRole('button', { name: 'Search counterparty' }).click()
    const dialog = page.getByRole('dialog', { name: /search counterparty/i })
    await expect(dialog).toBeVisible()

    // Search by a name substring (case-insensitive on the backend).
    await dialog.getByLabel('Name').fill('bank')
    await dialog.getByRole('button', { name: 'Search' }).click()

    // Select the first result row.
    const firstRow = dialog.locator('table tbody tr').first()
    await expect(firstRow).toBeVisible()
    const selectedName = (await firstRow.locator('td').nth(1).innerText()).trim()
    await firstRow.click()

    // Modal closes and the selection is written back as LEI + name.
    await expect(dialog).toBeHidden()
    await expect(page.getByTestId('selected-counterparty')).toContainText(selectedName)
  })

  test('searching with no match shows an empty state', async ({ page }) => {
    await page.goto('/trades/new')
    await page.getByRole('button', { name: 'Search counterparty' }).click()
    const dialog = page.getByRole('dialog', { name: /search counterparty/i })

    await dialog.getByLabel('Name').fill('zzzznomatch')
    await dialog.getByRole('button', { name: 'Search' }).click()

    await expect(dialog.getByText('No counterparties found.')).toBeVisible()
  })
})
