# Copilot Instructions — ProShop MERN

## 1. Overview

ProShop is a full-stack e-commerce application built on the MERN stack (MongoDB, Express, React, Node.js). It supports product browsing with search and pagination, user authentication with JWT, shopping cart, PayPal checkout, product reviews, and an admin panel for managing users, products, and orders. The backend serves a REST API consumed by a React/Redux single-page application. Originally authored by Brad Traversy as a course project; deployed on Heroku.

## 2. Tech Stack

| Layer         | Technology                      | Version     |
|---------------|---------------------------------|-------------|
| Runtime       | Node.js                         | ≥12         |
| Backend       | Express                         | ^4.17       |
| Database      | MongoDB + Mongoose              | ^5.10       |
| Auth          | jsonwebtoken + bcryptjs         | ^8.5 / ^2.4 |
| Upload        | Multer                          | ^1.4        |
| Frontend      | React (CRA)                     | ^16.13      |
| State         | Redux + Redux Thunk             | ^4.0 / ^2.3 |
| UI            | React-Bootstrap                 | ^1.3        |
| Routing       | React Router DOM v5             | ^5.2        |
| HTTP          | Axios                           | ^0.20       |
| Module system | ES Modules (`"type": "module"`) | —           |

## 3. Architecture

```
proshop_mern/
├── backend/
│   ├── config/db.js              # Mongoose connection
│   ├── controllers/              # Request handlers (product, user, order)
│   ├── data/                     # Seed data (users.js, products.js)
│   ├── middleware/
│   │   ├── authMiddleware.js     # protect, admin guards
│   │   └── errorMiddleware.js    # notFound, errorHandler
│   ├── models/                   # Mongoose schemas (User, Product, Order)
│   ├── routes/                   # Express routers (product, user, order, upload)
│   ├── utils/generateToken.js    # JWT helper
│   ├── seeder.js                 # DB seed/destroy script
│   └── server.js                 # ★ Express entry point
├── frontend/
│   ├── public/
│   └── src/
│       ├── actions/              # Redux thunk action creators
│       ├── constants/            # Action type string constants
│       ├── reducers/             # Redux reducers
│       ├── components/           # Reusable UI (Header, Footer, Loader, Rating…)
│       ├── screens/              # Page-level components (15 screens)
│       ├── store.js              # Redux store configuration
│       ├── App.js                # Router & layout
│       └── index.js              # ★ React entry point
├── uploads/                      # User-uploaded images (served statically)
├── package.json                  # Root: backend deps + dev scripts
├── Procfile                      # Heroku start command
└── .env                          # Environment variables (not committed)
```

**API base path:** `/api` — endpoints: `/api/products`, `/api/users`, `/api/orders`, `/api/upload`, `/api/config/paypal`.

## 4. Commands

```bash
# Install deps (root = backend; frontend has its own package.json)
npm install && npm install --prefix frontend

# Development (concurrently: Express + CRA dev server)
npm run dev

# Backend only (nodemon)
npm run server

# Frontend only (CRA)
npm run client

# Seed database
npm run data:import      # import sample data
npm run data:destroy     # wipe all collections

# Frontend build (production)
npm run build --prefix frontend

# Frontend tests
npm test --prefix frontend
```

> There is **no linter, formatter, or backend test suite** configured. Frontend uses CRA's default ESLint (`eslint-config-react-app`) and Jest/RTL scaffolding but has no written tests.

## 5. Conventions

### 5.1 File Naming
- **Backend:** camelCase — `productController.js`, `authMiddleware.js`, `userModel.js`.
- **Frontend components/screens:** PascalCase — `HomeScreen.js`, `Product.js`.
- **Frontend logic:** camelCase — `cartActions.js`, `userReducers.js`, `productConstants.js`.

### 5.2 Imports & Exports
- ES Modules everywhere (`import`/`export`). Backend files use `.js` extension in imports.
- **Models & components:** `export default`.
- **Controller functions:** named export block — `export { fn1, fn2, fn3 }`.
- **Constants:** individual named exports — `export const PRODUCT_LIST_REQUEST = '…'`.

### 5.3 Backend Controller Pattern
Every controller function is wrapped with `express-async-handler` and preceded by a JSDoc-style comment block:
```js
// @desc    Fetch single product
// @route   GET /api/products/:id
// @access  Public
const getProductById = asyncHandler(async (req, res) => { … })
```

### 5.4 Error Handling
- **Backend:** set status code → `throw new Error('message')`. Global `errorHandler` middleware returns `{ message, stack }` (stack only in development).
- **Frontend actions:** `try/catch` with `error.response?.data.message ?? error.message`. Token failure triggers `dispatch(logout())`.

### 5.5 Redux Flow (Actions → Constants → Reducers)
- One file per domain in each of `actions/`, `constants/`, `reducers/`.
- Constant triplet: `DOMAIN_ACTION_REQUEST`, `_SUCCESS`, `_FAIL` (optional `_RESET`).
- Reducer shape: `{ loading, error, <data> }`.
- Authenticated requests: extract `userInfo.token` from `getState()`, pass as `Authorization: Bearer <token>`.
- Persistence: cart items, user info, shipping address, payment method stored in `localStorage`.

### 5.6 Screen Component Structure
```js
const ScreenName = ({ match, location, history }) => {
  // 1. Local state (useState)
  // 2. Redux hooks (useDispatch, useSelector)
  // 3. Side effects (useEffect → dispatch)
  // 4. Event handlers (*Handler suffix)
  // 5. Conditional renders (Loader / Message)
  // 6. Main JSX
}
export default ScreenName
```

### 5.7 Routing
- React Router v5 with `<Route>` inside `<Router>`.
- Route props destructured: `match.params`, `location.search`, `history.push`.
- Admin routes prefixed `/admin/`.

### 5.8 Auth
- JWT with 30-day expiry stored in `localStorage`.
- Backend middleware chain: `protect` (verifies token) → `admin` (checks `isAdmin` flag).
- Token sent via `Authorization: Bearer <token>` header.

## 6. What NOT To Do

### Do not skip `asyncHandler`
Every async route handler **must** be wrapped in `asyncHandler`. Naked `async (req, res)` will swallow errors silently.

### Do not put code after `throw`
There is an unreachable `return` after `throw new Error(…)` in `orderController.js`. Never place statements after `throw`.

### Do not forget `return` after `next()` in middleware
`userModel.js` pre-save hook calls `next()` without `return` when the password is not modified, risking double hashing. Always `return next()`.

### Do not pass user input directly to MongoDB `$regex`
`productController.js` feeds `req.query.keyword` straight into `$regex` — this is vulnerable to ReDoS. Escape special regex characters or use `$text` search.

### Do not commit `.env`
The `.gitignore` excludes `.env`, but verify it stays that way. Secrets (`JWT_SECRET`, `MONGO_URI`, `PAYPAL_CLIENT_ID`) must never be checked in.

### Do not accept uploads without size limits
`uploadRoutes.js` has no `limits` option on Multer — add `limits: { fileSize: <max> }`.

### Do not ignore request body validation
Controllers trust `req.body` without validation. Use a library (e.g., Joi, express-validator) or at minimum manual checks before writing to the database.

### Do not create new reducers/actions in a different style
Follow the existing `REQUEST/SUCCESS/FAIL` constant triplet and `asyncHandler` thunk pattern. Do not introduce Redux Toolkit, Zustand, or other state libraries without a full migration.

### Do not add class components
The entire frontend uses functional components with hooks. Keep it consistent.

### Do not use `require()`
The project is `"type": "module"`. Always use ES `import`/`export`.
