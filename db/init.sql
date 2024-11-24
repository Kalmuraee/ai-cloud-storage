-- AI Cloud Storage Project Database Initialization
-- This script initializes the database schema and data for all services

-- Set timezone and basic configuration
SET TIME ZONE 'UTC';
SET session_replication_role = 'replica';

------------------------------------------
-- Authentication Service Tables
------------------------------------------

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    username VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- User-Role mapping
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Role-Permission mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

------------------------------------------
-- Storage Service Tables
------------------------------------------

-- File metadata table
CREATE TABLE IF NOT EXISTS file_metadata (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    original_filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR NOT NULL,
    hash_md5 VARCHAR,
    hash_sha256 VARCHAR,
    owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    storage_backend VARCHAR NOT NULL DEFAULT 'minio',
    bucket_name VARCHAR NOT NULL,
    metadata JSONB
);

-- File sharing table
CREATE TABLE IF NOT EXISTS file_shares (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES file_metadata(id) ON DELETE CASCADE,
    shared_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    shared_with INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR NOT NULL DEFAULT 'read',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(file_id, shared_with)
);

-- File versions table
CREATE TABLE IF NOT EXISTS file_versions (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES file_metadata(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size BIGINT NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    comment VARCHAR,
    UNIQUE(file_id, version_number)
);

------------------------------------------
-- AI Processing Service Tables
------------------------------------------

-- AI Processing Jobs
CREATE TABLE IF NOT EXISTS ai_jobs (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES file_metadata(id) ON DELETE CASCADE,
    job_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    parameters JSONB,
    results JSONB
);

-- AI Model Registry
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    version VARCHAR NOT NULL,
    description TEXT,
    model_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    configuration JSONB,
    metrics JSONB
);

------------------------------------------
-- Analytics Service Tables
------------------------------------------

-- User Activity Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR NOT NULL,
    resource_type VARCHAR NOT NULL,
    resource_id VARCHAR,
    details JSONB,
    ip_address VARCHAR,
    user_agent VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- System Metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR NOT NULL,
    metric_value FLOAT NOT NULL,
    dimensions JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Initialize default permissions
INSERT INTO permissions (name, description) VALUES
    ('user:read', 'Read user information'),
    ('user:write', 'Create and update user information'),
    ('user:delete', 'Delete user accounts'),
    ('role:read', 'View roles and permissions'),
    ('role:write', 'Create and modify roles'),
    ('role:delete', 'Delete roles'),
    ('file:read', 'Read files and metadata'),
    ('file:write', 'Upload and modify files'),
    ('file:delete', 'Delete files'),
    ('file:share', 'Share files with other users'),
    ('system:admin', 'Full system administration'),
    ('ai:process', 'Process files with AI'),
    ('ai:model:read', 'View AI model information'),
    ('ai:model:write', 'Manage AI models'),
    ('storage:admin', 'Manage storage settings'),
    ('analytics:read', 'View analytics and reports'),
    ('analytics:write', 'Create and modify reports'),
    ('api:access', 'Access API endpoints')
ON CONFLICT (name) DO NOTHING;

-- Initialize default roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'System Administrator'),
    ('user', 'Standard User'),
    ('ai_processor', 'AI Processing Role'),
    ('storage_manager', 'Storage Management Role'),
    ('analyst', 'Analytics and Reporting Role')
ON CONFLICT (name) DO NOTHING;

-- Assign permissions to roles
-- Admin role (all permissions)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p 
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Standard user permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'user'
AND p.name IN (
    'user:read',
    'file:read',
    'file:write',
    'file:delete',
    'file:share',
    'ai:process',
    'api:access'
)
ON CONFLICT DO NOTHING;

-- Create default admin user (password: admin123)
INSERT INTO users (
    email, username, hashed_password, full_name,
    is_active, is_superuser, is_verified
) VALUES (
    'admin@aicloud.local',
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'System Administrator',
    true, true, true
)
ON CONFLICT (email) DO NOTHING;

-- Assign admin role to admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_file_metadata_owner ON file_metadata(owner_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_created ON file_metadata(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_status ON ai_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_created ON ai_jobs(created_at);

-- Re-enable triggers
SET session_replication_role = 'origin';

-- Verify initialization
SELECT 'Database initialization completed successfully' as status;
SELECT 
    (SELECT COUNT(*) FROM users) as user_count,
    (SELECT COUNT(*) FROM roles) as role_count,
    (SELECT COUNT(*) FROM permissions) as permission_count,
    (SELECT COUNT(*) FROM role_permissions) as role_permission_count;
