import { ReactNode } from 'react'
import Navigation from './Navigation'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 py-8">{children}</div>
      </main>
    </div>
  )
}
