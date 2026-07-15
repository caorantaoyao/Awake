# 真实邮箱密码登录 Spec

## Why
当前登录只验证邮箱是否存在，不能证明操作者拥有该账号。为了实现真正的账号认证，需要在现有注册、登录、会话恢复流程中加入密码哈希存储与校验，同时兼容已经注册但没有密码的老用户。

## What Changes
- 在 `students` 表新增 `password_hash` 字段，存储不可逆密码哈希。
- 注册接口新增密码字段，注册时哈希后写入 `password_hash`。
- 登录接口新增密码字段，登录时校验密码哈希，邮箱不存在与密码错误分别返回可理解错误。
- 增加迁移脚本，为已有老用户补充可登录的密码哈希。
- 前端注册页新增密码设置与确认输入，登录页新增密码输入。
- 前端表单保留现有 Awaken 品牌视觉，错误提示清晰、键盘可用、移动端可用。
- **BREAKING**：新注册请求必须提供密码；登录请求必须提供邮箱与密码。

## Impact
- Affected specs: 学生注册、用户登录、会话恢复、前端注册/登录表单、测试数据库初始化。
- Affected code:
  - `backend/app/models/models.py`
  - `backend/app/schemas/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/auth_service.py`
  - `backend/app/core/database.py` 或独立迁移脚本
  - `backend/tests/test_api.py`
  - `frontend/src/pages/Register.jsx`
  - `frontend/src/pages/Login.jsx`
  - `frontend/src/api/client.js`
  - `frontend/src/styles/global.css`（仅在现有样式不足时最小补充）

## ADDED Requirements

### Requirement: Password Hash Storage
The system SHALL store user passwords only as password hashes in `students.password_hash`.

#### Scenario: New registration stores a hash
- **WHEN** a user registers with name, email, grade, and password
- **THEN** the database stores a non-empty `password_hash`
- **AND** the raw password is never returned in API responses
- **AND** the raw password is not stored in the `students` table

### Requirement: Password Registration
The system SHALL require password and password confirmation on the registration page.

#### Scenario: Registration success
- **WHEN** a user submits valid name, email, grade, password, and matching confirmation
- **THEN** registration succeeds using the existing student data shape
- **AND** the success page continues to work

#### Scenario: Password validation failure
- **WHEN** password is missing, too short, or confirmation does not match
- **THEN** the frontend displays an inline error
- **AND** no registration request is sent for frontend-caught validation errors

### Requirement: Password Login
The system SHALL authenticate login requests by verifying the submitted password against `password_hash`.

#### Scenario: Login success
- **WHEN** a registered user submits the correct email and password
- **THEN** the API returns a Bearer token and student profile
- **AND** the frontend stores the session and navigates to the chat experience

#### Scenario: Email not found
- **WHEN** a user submits an unregistered email
- **THEN** the API returns a not-found style error with a clear message

#### Scenario: Wrong password
- **WHEN** a user submits a registered email with the wrong password
- **THEN** the API returns an authentication error
- **AND** no token is issued

### Requirement: Legacy User Migration
The system SHALL provide a migration path for existing users without `password_hash`.

#### Scenario: Existing database is migrated
- **WHEN** the migration script runs against an existing SQLite database
- **THEN** `students.password_hash` exists
- **AND** students with missing password hashes receive a generated hash
- **AND** the migration is idempotent

### Requirement: Frontend Visual Quality
The registration and login forms SHALL remain visually consistent with Awaken’s current refined blue-and-white brand.

#### Scenario: Form interaction
- **WHEN** users focus password fields, submit invalid values, or view errors
- **THEN** field states are visible, readable, and consistent with existing form styles
- **AND** the page remains usable on mobile widths

## MODIFIED Requirements

### Requirement: Existing Registration Flow
Registration SHALL keep the existing name, email, and grade data contract while adding a required password field. Existing duplicate-email and grade validation behavior SHALL remain unchanged.

### Requirement: Existing Login Flow
Login SHALL no longer be passwordless. The API SHALL require both email and password, verify the stored hash, and only issue tokens after successful verification.

### Requirement: Existing Chat Entry Compatibility
The existing `/chat?email=...` path MAY remain temporarily compatible for email-link flows, but token-based login SHALL use authenticated session recovery when no email query parameter is present.

## REMOVED Requirements

### Requirement: Passwordless Login
**Reason**: Email-only login does not authenticate account ownership.
**Migration**: Replace email-only login with email-plus-password login. Preserve token creation and current-user recovery after password verification succeeds.
