import React, { useState, useEffect } from 'react'
import { Table, Badge } from 'react-bootstrap'
import { useSelector } from 'react-redux'
import axios from 'axios'
import Message from '../components/Message'
import Loader from '../components/Loader'

const FeatureListScreen = ({ history }) => {
    const [features, setFeatures] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const userLogin = useSelector((state) => state.userLogin)
    const { userInfo } = userLogin

    useEffect(() => {
        if (!userInfo || !userInfo.isAdmin) {
            history.push('/login')
            return
        }

        const fetchFeatures = async () => {
            try {
                const { data } = await axios.get('/api/feature-flags')
                setFeatures(
                    Object.entries(data).map(([key, feature]) => ({
                        key,
                        ...feature,
                    }))
                )
                setLoading(false)
            } catch (err) {
                setError(
                    err.response && err.response.data.message
                        ? err.response.data.message
                        : err.message
                )
                setLoading(false)
            }
        }

        fetchFeatures()
    }, [history, userInfo])

    const statusVariant = (status) => {
        switch (status) {
            case 'Enabled':
                return 'success'
            case 'Disabled':
                return 'danger'
            case 'Testing':
                return 'warning'
            case 'Shadow':
                return 'secondary'
            default:
                return 'light'
        }
    }

    return (
        <>
            <h1>Feature Flags</h1>
            {loading ? (
                <Loader />
            ) : error ? (
                <Message variant='danger'>{error}</Message>
            ) : (
                <Table striped bordered hover responsive className='table-sm'>
                    <thead>
                        <tr>
                            <th>NAME</th>
                            <th>STATUS</th>
                            <th>TRAFFIC %</th>
                            <th>LAST MODIFIED</th>
                            <th>DEPENDENCIES</th>
                            <th>DESCRIPTION</th>
                        </tr>
                    </thead>
                    <tbody>
                        {features.map((feature) => (
                            <tr key={feature.key}>
                                <td>{feature.name}</td>
                                <td>
                                    <Badge variant={statusVariant(feature.status)}>
                                        {feature.status}
                                    </Badge>
                                </td>
                                <td>{feature.traffic_percentage}%</td>
                                <td>{feature.last_modified}</td>
                                <td>
                                    {feature.dependencies
                                        ? feature.dependencies.join(', ')
                                        : '—'}
                                </td>
                                <td>
                                    <small>{feature.description}</small>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}
        </>
    )
}

export default FeatureListScreen
