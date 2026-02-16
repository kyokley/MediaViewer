import React, { createContext, useContext, useState } from 'react'

interface PaginationState {
  currentPage: number
  limit: number
  total: number
  setCurrentPage: (page: number) => void
  setLimit: (limit: number) => void
  setTotal: (total: number) => void
  reset: () => void
}

const PaginationContext = createContext<PaginationState | undefined>(undefined)

export const usePagination = () => {
  const context = useContext(PaginationContext)
  if (!context) {
    throw new Error('usePagination must be used within PaginationProvider')
  }
  return context
}

interface PaginationProviderProps {
  children: React.ReactNode
  initialLimit?: number
}

export const PaginationProvider: React.FC<PaginationProviderProps> = ({
  children,
  initialLimit = 20,
}) => {
  const [currentPage, setCurrentPage] = useState(0)
  const [limit, setLimit] = useState(initialLimit)
  const [total, setTotal] = useState(0)

  const reset = () => {
    setCurrentPage(0)
    setLimit(initialLimit)
    setTotal(0)
  }

  const value: PaginationState = {
    currentPage,
    limit,
    total,
    setCurrentPage,
    setLimit,
    setTotal,
    reset,
  }

  return (
    <PaginationContext.Provider value={value}>
      {children}
    </PaginationContext.Provider>
  )
}
