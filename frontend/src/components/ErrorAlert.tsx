interface ErrorAlertProps {
  message: string
}

export default function ErrorAlert({ message }: ErrorAlertProps) {
  return (
    <div className="mb-4 p-4 bg-red-900/50 border border-red-700 text-red-200 rounded-lg">
      <p className="font-medium">Error</p>
      <p className="text-sm mt-1">{message}</p>
    </div>
  )
}
