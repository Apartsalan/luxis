"use client";

import * as React from "react";

import { useIsMobile } from "@/hooks/use-is-mobile";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";

// Eén component dat op desktop een gecentreerde Dialog toont en op telefoon een
// onderschuif-paneel (Drawer/Vaul). Bedoeld voor korte acties (notitie, taak,
// uren, filters). Grote formulieren kunnen de gewone Dialog blijven gebruiken —
// die is op telefoon al schermvullend (dialog.tsx max-sm-vangnet).
//
// API is opzettelijk identiek aan Dialog: `open`, `onOpenChange`, children met
// ResponsiveDialogHeader/Title/Description/Footer. De inhoud scrollt binnen het
// paneel; de footer blijft onderaan.

interface ResponsiveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

const MobileCtx = React.createContext(false);

export function ResponsiveDialog({ open, onOpenChange, children }: ResponsiveDialogProps) {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <MobileCtx.Provider value={true}>
        <Drawer open={open} onOpenChange={onOpenChange}>
          <DrawerContent>{children}</DrawerContent>
        </Drawer>
      </MobileCtx.Provider>
    );
  }

  return (
    <MobileCtx.Provider value={false}>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>{children}</DialogContent>
      </Dialog>
    </MobileCtx.Provider>
  );
}

export function ResponsiveDialogHeader(props: React.HTMLAttributes<HTMLDivElement>) {
  const isMobile = React.useContext(MobileCtx);
  return isMobile ? <DrawerHeader {...props} /> : <DialogHeader {...props} />;
}

export function ResponsiveDialogFooter(props: React.HTMLAttributes<HTMLDivElement>) {
  const isMobile = React.useContext(MobileCtx);
  return isMobile ? <DrawerFooter {...props} /> : <DialogFooter {...props} />;
}

export function ResponsiveDialogTitle(
  props: React.ComponentPropsWithoutRef<typeof DialogTitle>
) {
  const isMobile = React.useContext(MobileCtx);
  return isMobile ? <DrawerTitle {...props} /> : <DialogTitle {...props} />;
}

export function ResponsiveDialogDescription(
  props: React.ComponentPropsWithoutRef<typeof DialogDescription>
) {
  const isMobile = React.useContext(MobileCtx);
  return isMobile ? <DrawerDescription {...props} /> : <DialogDescription {...props} />;
}

// Scrollbaar middenblok tussen header en footer (op telefoon krijgt de Drawer een
// begrensde hoogte; deze wrapper laat alleen de body scrollen).
export function ResponsiveDialogBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  const isMobile = React.useContext(MobileCtx);
  return (
    <div
      className={
        isMobile
          ? `overflow-y-auto px-4 ${className ?? ""}`
          : className
      }
      {...props}
    />
  );
}
