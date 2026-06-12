const express = require('express');
const app = express();
const authRouter = require('./auth/router');
const notificationsRouter = require('./notifications/router');
app.use(express.json());
app.use('/api/auth', authRouter);
app.use('/api/notifications', notificationsRouter);
module.exports = app;