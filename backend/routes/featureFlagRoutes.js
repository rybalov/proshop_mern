import express from 'express'
import {
    getFeatureFlags,
    getFeatureFlagByName,
} from '../controllers/featureFlagController.js'

const router = express.Router()

router.route('/').get(getFeatureFlags)
router.route('/:name').get(getFeatureFlagByName)

export default router
