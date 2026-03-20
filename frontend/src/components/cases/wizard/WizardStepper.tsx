import { Fragment } from "react";
import { Check } from "lucide-react";

export function WizardStepper({
  currentStep,
  steps,
  onStepClick,
}: {
  currentStep: number;
  steps: { label: string; optional?: boolean }[];
  onStepClick: (step: number) => void;
}) {
  return (
    <div className="flex items-center">
      {steps.map((step, index) => {
        const stepNum = index + 1;
        const isActive = stepNum === currentStep;
        const isCompleted = stepNum < currentStep;
        const isClickable = stepNum < currentStep;

        return (
          <Fragment key={index}>
            <button
              type="button"
              onClick={() => isClickable && onStepClick(stepNum)}
              className={`flex items-center gap-2 transition-colors ${
                isClickable ? "cursor-pointer" : isActive ? "cursor-default" : "cursor-default"
              }`}
            >
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : isCompleted
                    ? "bg-primary/10 text-primary"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : stepNum}
              </span>
              <span
                className={`hidden sm:inline text-sm font-medium ${
                  isActive
                    ? "text-foreground"
                    : isCompleted
                    ? "text-primary"
                    : "text-muted-foreground"
                }`}
              >
                {step.label}
                {step.optional && (
                  <span className="text-[11px] text-muted-foreground font-normal">
                    {" "}(optioneel)
                  </span>
                )}
              </span>
            </button>
            {index < steps.length - 1 && (
              <div
                className={`mx-3 h-px flex-1 transition-colors ${
                  stepNum < currentStep ? "bg-primary" : "bg-border"
                }`}
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
