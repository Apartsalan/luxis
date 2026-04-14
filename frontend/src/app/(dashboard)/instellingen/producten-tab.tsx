"use client";

import { useState } from "react";
import {
  Package,
  Loader2,
  Download,
  Pencil,
  Trash2,
  Plus,
  Check,
  X,
} from "lucide-react";
import { toast } from "sonner";
import {
  useProducts,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
  useSeedProducts,
  Product,
  ProductCreate,
} from "@/hooks/use-products";

const VAT_TYPE_LABELS: Record<string, string> = {
  "21": "21% BTW",
  "0": "Geen BTW",
  eu: "Binnen EU",
  non_eu: "Buiten EU",
};

function EmptyState({ onSeed }: { onSeed: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Package className="h-12 w-12 text-muted-foreground/50 mb-4" />
      <h3 className="text-lg font-semibold text-foreground mb-1">
        Geen producten
      </h3>
      <p className="text-sm text-muted-foreground mb-4 max-w-md">
        Importeer de 28 standaard Basenet-artikelen om te beginnen, of maak
        handmatig producten aan.
      </p>
      <button
        onClick={onSeed}
        className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <Download className="h-4 w-4" />
        Basenet-artikelen importeren
      </button>
    </div>
  );
}

function ProductRow({
  product,
  onEdit,
  onDelete,
}: {
  product: Product;
  onEdit: (p: Product) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <tr className="border-b border-border/50 hover:bg-muted/30 transition-colors">
      <td className="px-3 py-2.5 text-sm font-mono text-muted-foreground">
        {product.code}
      </td>
      <td className="px-3 py-2.5 text-sm font-medium text-foreground">
        {product.name}
      </td>
      <td className="px-3 py-2.5 text-sm text-muted-foreground">
        {product.default_price != null
          ? `€ ${Number(product.default_price).toFixed(2)}`
          : "—"}
      </td>
      <td className="px-3 py-2.5 text-sm text-muted-foreground">
        {product.gl_account_code}
      </td>
      <td className="px-3 py-2.5 text-sm text-muted-foreground max-w-[200px] truncate">
        {product.gl_account_name}
      </td>
      <td className="px-3 py-2.5">
        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-muted text-muted-foreground">
          {VAT_TYPE_LABELS[product.vat_type] || product.vat_type}
        </span>
      </td>
      <td className="px-3 py-2.5 text-right">
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={() => onEdit(product)}
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Bewerken"
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => onDelete(product.id)}
            className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
            title="Verwijderen"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </td>
    </tr>
  );
}

function ProductForm({
  initial,
  onSave,
  onCancel,
  saving,
}: {
  initial?: Product;
  onSave: (data: ProductCreate) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<ProductCreate>({
    code: initial?.code || "",
    name: initial?.name || "",
    description: initial?.description || "",
    default_price: initial?.default_price ?? undefined,
    gl_account_code: initial?.gl_account_code || "",
    gl_account_name: initial?.gl_account_name || "",
    vat_type: initial?.vat_type || "21",
    vat_percentage: initial?.vat_percentage ?? 21,
    sort_order: initial?.sort_order ?? 0,
  });

  return (
    <tr className="border-b border-primary/20 bg-primary/5">
      <td className="px-3 py-2">
        <input
          className="w-full rounded border border-input bg-background px-2 py-1 text-sm"
          placeholder="Code"
          value={form.code}
          onChange={(e) => setForm({ ...form, code: e.target.value })}
        />
      </td>
      <td className="px-3 py-2">
        <input
          className="w-full rounded border border-input bg-background px-2 py-1 text-sm"
          placeholder="Naam"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
      </td>
      <td className="px-3 py-2">
        <input
          className="w-24 rounded border border-input bg-background px-2 py-1 text-sm"
          placeholder="Prijs"
          type="number"
          step="0.01"
          value={form.default_price ?? ""}
          onChange={(e) =>
            setForm({
              ...form,
              default_price: e.target.value ? Number(e.target.value) : undefined,
            })
          }
        />
      </td>
      <td className="px-3 py-2">
        <input
          className="w-20 rounded border border-input bg-background px-2 py-1 text-sm"
          placeholder="GL code"
          value={form.gl_account_code}
          onChange={(e) => setForm({ ...form, gl_account_code: e.target.value })}
        />
      </td>
      <td className="px-3 py-2">
        <input
          className="w-full rounded border border-input bg-background px-2 py-1 text-sm"
          placeholder="GL naam"
          value={form.gl_account_name}
          onChange={(e) => setForm({ ...form, gl_account_name: e.target.value })}
        />
      </td>
      <td className="px-3 py-2">
        <select
          className="rounded border border-input bg-background px-2 py-1 text-sm"
          value={form.vat_type}
          onChange={(e) => {
            const vt = e.target.value;
            const pct =
              vt === "21" ? 21 : vt === "0" ? 0 : 0;
            setForm({ ...form, vat_type: vt, vat_percentage: pct });
          }}
        >
          <option value="21">21% BTW</option>
          <option value="0">Geen BTW</option>
          <option value="eu">Binnen EU</option>
          <option value="non_eu">Buiten EU</option>
        </select>
      </td>
      <td className="px-3 py-2 text-right">
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={() => onSave(form)}
            disabled={saving || !form.code || !form.name || !form.gl_account_code}
            className="rounded p-1 text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
            title="Opslaan"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={onCancel}
            className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Annuleren"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  );
}

export function ProductenTab() {
  const { data: products, isLoading } = useProducts(false);
  const createProduct = useCreateProduct();
  const updateProduct = useUpdateProduct();
  const deleteProduct = useDeleteProduct();
  const seedProducts = useSeedProducts();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [showNewRow, setShowNewRow] = useState(false);

  const handleSeed = async () => {
    try {
      const result = await seedProducts.mutateAsync();
      toast.success(result.message);
    } catch {
      toast.error("Importeren mislukt");
    }
  };

  const handleCreate = async (data: ProductCreate) => {
    try {
      await createProduct.mutateAsync(data);
      setShowNewRow(false);
      toast.success("Product aangemaakt");
    } catch {
      toast.error("Aanmaken mislukt");
    }
  };

  const handleUpdate = async (data: ProductCreate) => {
    if (!editingId) return;
    try {
      await updateProduct.mutateAsync({ id: editingId, ...data });
      setEditingId(null);
      toast.success("Product bijgewerkt");
    } catch {
      toast.error("Bijwerken mislukt");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteProduct.mutateAsync(id);
      toast.success("Product verwijderd");
    } catch {
      toast.error("Verwijderen mislukt");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!products?.length && !showNewRow) {
    return <EmptyState onSeed={handleSeed} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            Producten & artikelen
          </h2>
          <p className="text-sm text-muted-foreground">
            Artikelcatalogus met grootboekrekeningen voor Exact Online
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSeed}
            disabled={seedProducts.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg border border-input bg-background px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            {seedProducts.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5" />
            )}
            Basenet import
          </button>
          <button
            onClick={() => setShowNewRow(true)}
            disabled={showNewRow}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Plus className="h-3.5 w-3.5" />
            Nieuw product
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-20">
                  Code
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Naam
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-24">
                  Prijs
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-20">
                  GB-code
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Grootboekrekening
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-24">
                  BTW
                </th>
                <th className="px-3 py-2 w-16" />
              </tr>
            </thead>
            <tbody>
              {showNewRow && (
                <ProductForm
                  onSave={handleCreate}
                  onCancel={() => setShowNewRow(false)}
                  saving={createProduct.isPending}
                />
              )}
              {products?.map((product) =>
                editingId === product.id ? (
                  <ProductForm
                    key={product.id}
                    initial={product}
                    onSave={handleUpdate}
                    onCancel={() => setEditingId(null)}
                    saving={updateProduct.isPending}
                  />
                ) : (
                  <ProductRow
                    key={product.id}
                    product={product}
                    onEdit={(p) => setEditingId(p.id)}
                    onDelete={handleDelete}
                  />
                )
              )}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {products?.length || 0} producten &middot; Grootboekrekeningen worden
        automatisch meegegeven bij Exact Online sync
      </p>
    </div>
  );
}
