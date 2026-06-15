import React from 'react'

import Button from './Button'
import Card from './Card'

export default class RouteErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || 'Unexpected page error' }
  }

  componentDidCatch(error, info) {
    console.error('Route boundary caught error', error, info)
  }

  handleReset = () => {
    this.setState({ hasError: false, message: '' })
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card role="alert" aria-live="assertive">
          <h2 className="text-lg font-semibold text-gray-100">Page failed to render</h2>
          <p className="mt-2 text-sm text-rose-300">{this.state.message}</p>
          <Button className="mt-4" onClick={this.handleReset}>
            Retry Page
          </Button>
        </Card>
      )
    }

    return this.props.children
  }
}
