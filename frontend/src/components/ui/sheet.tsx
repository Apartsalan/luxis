"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

// ── Zijpaneel (S233) ─────────────────────────────────────────────────────────
// Een rechts-verankerd paneel op basis van Radix Dialog. Anders dan een gewone
// Dialog is dit NIET-modaal: er is geen verduisterende overlay die klikken
// blokkeert, zodat links de mails leesbaar én aanklikbaar blijven terwijl je in
// het paneel schrijft. Sluiten gaat via de X/Annuleren of Escape — een klik
// buiten het paneel sluit het bewust NIET (anders zou het aanklikken van een mail
// links het paneel wegklappen).
//
// Op telefoon (<sm) vult het paneel het hele scherm (net als de oude compose-
// dialog), met een veilige onderrand.

const Sheet = ({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Root>) => (
  // modal={false} → geen scroll-lock en geen klik-blokkade op de rest van de pagina.
  <DialogPrimitive.Root modal={false} {...props} />
);
Sheet.displayName = "Sheet";

const SheetTrigger = DialogPrimitive.Trigger;
const SheetClose = DialogPrimitive.Close;
const SheetPortal = DialogPrimitive.Portal;

const SheetContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, onInteractOutside, ...props }, ref) => (
  <SheetPortal>
    <DialogPrimitive.Content
      ref={ref}
      // Buiten-klik mag het paneel niet sluiten (anders klapt het weg zodra je
      // links een mail aanklikt). De aanroeper kan onInteractOutside alsnog
      // meegeven; wij roepen die eerst aan en blokkeren daarna standaard.
      onInteractOutside={(e) => {
        onInteractOutside?.(e);
        e.preventDefault();
      }}
      className={cn(
        "fixed inset-y-0 right-0 z-50 flex h-full w-full flex-col border-l bg-background shadow-lg",
        "sm:max-w-xl md:max-w-2xl",
        "duration-300 data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right",
        // Telefoon: schermvullend, veilige onderrand.
        "max-sm:max-w-none max-sm:border-l-0 max-sm:pb-[env(safe-area-inset-bottom)]",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none">
        <X className="h-4 w-4" />
        <span className="sr-only">Sluiten</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </SheetPortal>
));
SheetContent.displayName = "SheetContent";

const SheetTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-base font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
SheetTitle.displayName = DialogPrimitive.Title.displayName;

const SheetDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
SheetDescription.displayName = DialogPrimitive.Description.displayName;

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetPortal,
  SheetContent,
  SheetTitle,
  SheetDescription,
};
