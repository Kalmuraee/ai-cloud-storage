describe('AI Cloud Storage E2E Tests', () => {
  beforeEach(() => {
    // Reset state and login before each test
    cy.request('POST', '/api/v1/test/reset-state')
    cy.login('test_user', 'test_password')
  })

  it('should upload and process a file', () => {
    // Visit home page
    cy.visit('/')
    
    // Upload file
    cy.get('[data-testid="upload-button"]').click()
    cy.get('input[type="file"]').attachFile('test-files/sample.pdf')
    cy.get('[data-testid="upload-submit"]').click()
    
    // Wait for processing
    cy.get('[data-testid="processing-status"]', { timeout: 10000 })
      .should('contain', 'Processing complete')
    
    // Verify file appears in list
    cy.get('[data-testid="file-list"]')
      .should('contain', 'sample.pdf')
  })

  it('should perform semantic search', () => {
    cy.visit('/search')
    
    // Enter search query
    cy.get('[data-testid="search-input"]')
      .type('machine learning documents{enter}')
    
    // Wait for results
    cy.get('[data-testid="search-results"]', { timeout: 10000 })
      .should('be.visible')
      .and('not.be.empty')
    
    // Verify result relevance
    cy.get('[data-testid="search-result"]').first()
      .should('contain', 'machine learning')
  })

  it('should process files with AI', () => {
    cy.visit('/files')
    
    // Select file
    cy.get('[data-testid="file-checkbox"]').first().click()
    
    // Open AI processing menu
    cy.get('[data-testid="ai-process-button"]').click()
    
    // Select operations
    cy.get('[data-testid="operation-summarize"]').click()
    cy.get('[data-testid="operation-analyze"]').click()
    
    // Start processing
    cy.get('[data-testid="process-submit"]').click()
    
    // Wait for completion
    cy.get('[data-testid="processing-status"]', { timeout: 20000 })
      .should('contain', 'Complete')
    
    // Verify results
    cy.get('[data-testid="ai-results"]')
      .should('contain', 'Summary')
      .and('contain', 'Analysis')
  })

  it('should handle batch operations', () => {
    cy.visit('/files')
    
    // Select multiple files
    cy.get('[data-testid="file-checkbox"]').first().click()
    cy.get('[data-testid="file-checkbox"]').eq(1).click()
    
    // Start batch process
    cy.get('[data-testid="batch-process-button"]').click()
    cy.get('[data-testid="batch-operation-summarize"]').click()
    cy.get('[data-testid="batch-submit"]').click()
    
    // Verify batch progress
    cy.get('[data-testid="batch-progress"]', { timeout: 30000 })
      .should('contain', '100%')
  })

  it('should manage file permissions', () => {
    cy.visit('/files')
    
    // Select file
    cy.get('[data-testid="file-menu"]').first().click()
    cy.get('[data-testid="share-button"]').click()
    
    // Add user permission
    cy.get('[data-testid="add-user-input"]')
      .type('share_user@example.com')
    cy.get('[data-testid="permission-select"]')
      .select('read')
    cy.get('[data-testid="add-permission"]').click()
    
    // Verify permission added
    cy.get('[data-testid="permissions-list"]')
      .should('contain', 'share_user@example.com')
      .and('contain', 'Read')
  })
})

// Custom commands
Cypress.Commands.add('login', (username: string, password: string) => {
  cy.request('POST', '/api/v1/auth/login', {
    username,
    password
  }).then((response) => {
    window.localStorage.setItem('token', response.body.access_token)
  })
})
