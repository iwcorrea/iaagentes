const express = require('express');
const router = express.Router();
const notificationsController = require('../controllers/notificationsController');
router.get('/', notificationsController.getAll);
router.post('/', notificationsController.create);
router.put('/:id', notificationsController.update);
router.delete('/:id', notificationsController.delete);
module.exports = router;