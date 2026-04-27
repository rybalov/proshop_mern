# ProShop MERN

E-commerce platform for browsing products, managing a shopping cart, and placing orders with PayPal checkout. Includes an admin panel for product, user, and order management. Built as a monorepo: an Express REST API backed by MongoDB on the server side, and a React/Redux single-page application on the client side. Originally created by Brad Traversy as a Udemy course project.

> **Note:** The upstream repository is archived. The author recommends [proshop-v2](https://github.com/bradtraversy/proshop-v2) (Redux Toolkit). This fork is maintained independently.

![screenshot](https://github.com/bradtraversy/proshop_mern/blob/master/uploads/Screen%20Shot%202020-09-29%20at%205.50.52%20PM.png)

## Tech Stack

| Layer       | Package                  | Version         |
|-------------|--------------------------|-----------------|
| Runtime     | Node.js (ES Modules)     | ≥14.6           |
| Backend     | Express                  | ^4.17.1         |
| Database    | Mongoose (MongoDB)       | ^5.10.6         |
| Auth        | jsonwebtoken / bcryptjs  | ^8.5.1 / ^2.4.3 |
| File upload | Multer                   | ^1.4.2          |
| Frontend    | React (Create React App) | ^16.13.1        |
| State       | Redux + Redux Thunk      | ^4.0.5 / ^2.3.0 |
| UI          | React-Bootstrap          | ^1.3.0          |
| Routing     | react-router-dom         | ^5.2.0          |
| HTTP client | Axios                    | ^0.20.0         |
| Dev tools   | concurrently, nodemon    | ^5.3.0 / ^2.0.4 |

## Folder Structure

```
proshop_mern/
├── backend/
│   ├── config/db.js            # Mongoose connection (MONGO_URI)
│   ├── controllers/            # Route handlers: product, user, order
│   ├── data/                   # Seed data: users.js, products.js
│   ├── middleware/
│   │   ├── authMiddleware.js   # JWT verify (protect) + admin guard
│   │   └── errorMiddleware.js  # 404 handler + global error handler
│   ├── models/                 # Mongoose schemas: User, Product, Order
│   ├── routes/                 # Express routers: product, user, order, upload
│   ├── utils/generateToken.js  # JWT sign helper (30-day expiry)
│   ├── seeder.js               # Import / destroy sample data
│   └── server.js               # Express entry point
├── frontend/
│   └── src/
│       ├── actions/            # Redux Thunk action creators (4 files)
│       ├── constants/          # Action type strings (4 files)
│       ├── reducers/           # Redux reducers (4 files)
│       ├── components/         # Reusable UI: Header, Footer, Loader, Rating, etc.
│       ├── screens/            # Page components (15 screens)
│       ├── store.js            # Redux store with localStorage hydration
│       ├── App.js              # React Router layout
│       └── index.js            # React entry point
├── uploads/                    # User-uploaded product images (served at /uploads)
├── package.json                # Root: backend deps + monorepo scripts
├── Procfile                    # Heroku: web: node backend/server.js
└── .env                        # Environment variables (not committed)
```

## Prerequisites

- **Node.js** ≥ 14.6 (ES Modules support required; tested with Node 16/18)
- **MongoDB** — any one of:
  - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) free tier (M0) — no local installation needed
  - Local `mongod` (Community Server 4.4+)
  - Docker: `docker run -d -p 27017:27017 --name mongo mongo:6`

## Environment Variables

Create a `.env` file in the **project root** (not inside `backend/`). Every variable below is read by the code at runtime:

```env
NODE_ENV=development
PORT=5000
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/proshop?retryWrites=true&w=majority
JWT_SECRET=<any-random-string>
PAYPAL_CLIENT_ID=<your-paypal-sandbox-client-id>
```

| Variable           | Where used                              | Notes                                                                                         |
|--------------------|-----------------------------------------|-----------------------------------------------------------------------------------------------|
| `NODE_ENV`         | `server.js`, `errorMiddleware.js`       | `development` enables morgan logger and error stacks                                          |
| `PORT`             | `server.js`                             | **Must be `5000`** — frontend proxy (`frontend/package.json`) targets `http://127.0.0.1:5000` |
| `MONGO_URI`        | `config/db.js`                          | Full connection string including database name                                                |
| `JWT_SECRET`       | `generateToken.js`, `authMiddleware.js` | Used to sign and verify JWT tokens                                                            |
| `PAYPAL_CLIENT_ID` | `server.js` (`/api/config/paypal`)      | Served to frontend for PayPal SDK initialization                                              |

## Installation & Startup

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd proshop_mern

# 2. Install backend dependencies (root package.json)
npm install

# 3. Install frontend dependencies
npm install --prefix frontend

# 4. Create .env (see table above)
cp .env.example .env   # or create manually

# 5. (Optional) Seed the database with sample data
npm run data:import

# 6. Start both servers in dev mode
npm run dev
```

After `npm run dev`:
- **Backend API** → `http://localhost:5000` (Express + nodemon)
- **Frontend** → `http://localhost:3000` (CRA dev server, proxied to backend)

### Other Commands

| Command                           | What it does                                    |
|-----------------------------------|-------------------------------------------------|
| `npm run server`                  | Backend only (nodemon, watches for changes)     |
| `npm run client`                  | Frontend only (CRA dev server)                  |
| `npm run data:import`             | Wipes DB, inserts sample users + products       |
| `npm run data:destroy`            | Wipes all collections (users, products, orders) |
| `npm run build --prefix frontend` | Production build of the frontend                |

### Sample Logins (after seeding)

| Email               | Password | Role     |
|---------------------|----------|----------|
| `admin@example.com` | `123456` | Admin    |
| `john@example.com`  | `123456` | Customer |
| `jane@example.com`  | `123456` | Customer |

## Troubleshooting

### Backend won't start / `ECONNREFUSED`
- Check that `MONGO_URI` in `.env` is correct and the database is reachable.
- For Atlas: whitelist your IP in Network Access (or use `0.0.0.0/0` for dev).
- For local MongoDB: make sure `mongod` is running (`brew services start mongodb-community` on macOS, `systemctl start mongod` on Linux).

### Frontend shows "Proxy error: Could not proxy request"
- The CRA dev server proxies to `http://127.0.0.1:5000` (set in `frontend/package.json`).
- Make sure `PORT=5000` in your `.env`. If you change the port, update the `"proxy"` field in `frontend/package.json` to match.

### PayPal button doesn't render / "Invalid client id"
- Create a sandbox app at [developer.paypal.com](https://developer.paypal.com/developer/applications/) → Sandbox → Create App.
- Copy the **Client ID** (not the secret) into `PAYPAL_CLIENT_ID` in `.env`.
- PayPal SDK is loaded on the client side from the `/api/config/paypal` endpoint. If the variable is empty, the button won't appear.

### `--openssl-legacy-provider` errors
- CRA 3.x + Node 17+ requires the `--openssl-legacy-provider` flag. This is already set in `frontend/package.json` scripts. If you still get OpenSSL errors, use Node 16 LTS or verify the flag is present.

### Image uploads fail silently
- The `uploads/` directory must exist in the project root. Create it if missing: `mkdir -p uploads`.
- Only `.jpg`, `.jpeg`, `.png` are accepted (checked by `uploadRoutes.js`).

### Mongoose deprecation warnings
- `useCreateIndex`, `useNewUrlParser`, `useUnifiedTopology` options in `config/db.js` are for Mongoose 5.x. If you upgrade to Mongoose 6+, remove these options (they are the defaults in v6).

## License

MIT — Copyright (c) 2020 Traversy Media.
