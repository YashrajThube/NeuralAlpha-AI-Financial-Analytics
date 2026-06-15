import Button from './Button'
import Card from './Card'

export default function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <Card className="border-dashed border-white/15 bg-white/5 text-center shadow-none hover:translate-y-0 hover:shadow-none">
      <div className="mx-auto max-w-md py-8">
        <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
        <p className="mt-2 text-sm text-gray-400">{description}</p>
        {actionLabel && onAction && (
          <Button className="mt-5" variant="outline" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </div>
    </Card>
  )
}