import { useState } from 'react'
import { FolderOpen, Plus, Trash2, Edit2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  useCollections,
  useCreateCollection,
  useUpdateCollection,
  useDeleteCollection,
} from '@/hooks/useCollections'
import type { Collection } from '@/types'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'

const COLORS = [
  '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b',
  '#ef4444', '#ec4899', '#06b6d4', '#84cc16',
]

interface CollectionFormState {
  name: string
  description: string
  color: string
}

export default function CollectionsPage() {
  const { data: collections, isLoading } = useCollections()
  const { mutate: createCollection, isPending: isCreating } = useCreateCollection()
  const { mutate: updateCollection, isPending: isUpdating } = useUpdateCollection()
  const { mutate: deleteCollection } = useDeleteCollection()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Collection | null>(null)
  const [form, setForm] = useState<CollectionFormState>({
    name: '',
    description: '',
    color: COLORS[0],
  })

  const openCreate = () => {
    setEditTarget(null)
    setForm({ name: '', description: '', color: COLORS[0] })
    setDialogOpen(true)
  }

  const openEdit = (c: Collection) => {
    setEditTarget(c)
    setForm({ name: c.name, description: c.description ?? '', color: c.color })
    setDialogOpen(true)
  }

  const handleSave = () => {
    if (!form.name.trim()) return

    if (editTarget) {
      updateCollection(
        { id: editTarget.id, ...form },
        {
          onSuccess: () => {
            toast.success('Collection updated')
            setDialogOpen(false)
          },
        },
      )
    } else {
      createCollection(form, {
        onSuccess: () => {
          toast.success('Collection created')
          setDialogOpen(false)
        },
      })
    }
  }

  const handleDelete = (id: string) => {
    if (!window.confirm('Delete this collection? Documents will not be removed.')) return
    deleteCollection(id, {
      onSuccess: () => toast.success('Collection deleted'),
    })
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Collections</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Organize documents into thematic groups
          </p>
        </div>
        <Button onClick={openCreate} size="sm">
          <Plus className="h-4 w-4 mr-2" />
          New Collection
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      ) : collections && collections.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((c) => (
            <Card key={c.id} className="group hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div
                      className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0"
                      style={{ background: c.color }}
                    />
                    <div>
                      <p className="text-sm font-semibold">{c.name}</p>
                      {c.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                          {c.description}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        {c.document_count} document{c.document_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => openEdit(c)}
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive"
                      onClick={() => handleDelete(c.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FolderOpen className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-sm font-medium">No collections yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Create a collection to organize your documents
            </p>
            <Button className="mt-4" size="sm" onClick={openCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Create first collection
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Create/Edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editTarget ? 'Edit Collection' : 'New Collection'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="col-name">Name *</Label>
              <Input
                id="col-name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Legal Documents"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="col-desc">Description</Label>
              <Textarea
                id="col-desc"
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Optional description…"
                rows={2}
              />
            </div>

            <div className="space-y-1.5">
              <Label>Color</Label>
              <div className="flex flex-wrap gap-2">
                {COLORS.map((color) => (
                  <button
                    key={color}
                    className={`w-7 h-7 rounded-full transition-transform ${
                      form.color === color ? 'ring-2 ring-offset-2 ring-foreground scale-110' : ''
                    }`}
                    style={{ background: color }}
                    onClick={() => setForm((f) => ({ ...f, color }))}
                  />
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!form.name.trim() || isCreating || isUpdating}
            >
              {editTarget ? 'Save Changes' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
