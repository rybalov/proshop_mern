import { readFileSync } from 'fs'
import path from 'path'

const __dirname = path.resolve()
const FEATURES_PATH = path.join(__dirname, 'backend', 'features.json')

function loadFeatures() {
    const raw = readFileSync(FEATURES_PATH, 'utf-8')
    return JSON.parse(raw)
}

// @desc    Get all feature flags
// @route   GET /api/feature-flags
// @access  Public
const getFeatureFlags = (req, res) => {
    try {
        const features = loadFeatures()
        res.json(features)
    } catch (error) {
        res.status(500).json({ message: 'Failed to read feature flags' })
    }
}

// @desc    Get a single feature flag by key
// @route   GET /api/feature-flags/:name
// @access  Public
const getFeatureFlagByName = (req, res) => {
    try {
        const features = loadFeatures()
        const feature = features[req.params.name]

        if (!feature) {
            res.status(404)
            throw new Error(`Feature '${req.params.name}' not found`)
        }

        res.json({ key: req.params.name, ...feature })
    } catch (error) {
        if (res.statusCode === 200) {
            res.status(500)
        }
        res.json({ message: error.message })
    }
}

export { getFeatureFlags, getFeatureFlagByName }
