/** Per-operation busy flags for popup, diff window, and options.
 *
 * UI is an execution-surface element (peer to LLM chat UIs); see docs/ui-design-principles.md.
 */

export type BusyState = {
  capturing: boolean;
  capturingClipboard: boolean;
  evaluating: boolean;
  loadingDiff: boolean;
  approving: boolean;
  rejecting: boolean;
  refreshingCandidates: boolean;
  insertingContext: boolean;
  pairing: boolean;
};

export type BusyKey = keyof BusyState;

export function createEmptyBusyState(): BusyState {
  return {
    capturing: false,
    capturingClipboard: false,
    evaluating: false,
    loadingDiff: false,
    approving: false,
    rejecting: false,
    refreshingCandidates: false,
    insertingContext: false,
    pairing: false,
  };
}

export function isBusyState(state: BusyState): boolean {
  return Object.values(state).some(Boolean);
}

export type BusyButtonBinding = {
  busyKey: BusyKey;
  idleLabel: string;
  busyLabel: string;
  /** When true, also disable while approve/reject runs (candidate actions). */
  blockDuringCandidateMutation?: boolean;
};

const BUSY_CURSOR_DELAY_MS = 150;

export type CursorHint = "busy" | "unavailable";

export function applyCursorHint(el: HTMLButtonElement, hint: CursorHint | null): void {
  if (hint) {
    el.setAttribute("data-cursor-hint", hint);
  } else {
    el.removeAttribute("data-cursor-hint");
  }
}

export function applyDisabledWithCursorHint(
  el: HTMLButtonElement,
  disabled: boolean,
  hint: CursorHint | null,
): void {
  el.disabled = disabled;
  applyCursorHint(el, disabled ? hint : null);
}

function resolveDisabledHint(
  disabled: boolean,
  busyBlock: boolean,
  globalBusy: boolean,
): CursorHint | null {
  if (!disabled) return null;
  if (busyBlock || globalBusy) return "busy";
  return "unavailable";
}

export class BusyUiController {
  private state: BusyState = createEmptyBusyState();
  private busyTimer: ReturnType<typeof setTimeout> | undefined;
  private readonly bindings = new Map<string, BusyButtonBinding & { el: HTMLButtonElement }>();
  private onStateChange?: (state: BusyState) => void;

  constructor(
    private readonly ariaRoot: HTMLElement,
    private readonly doc: Document = document,
  ) {}

  setOnStateChange(handler: (state: BusyState) => void): void {
    this.onStateChange = handler;
  }

  getState(): Readonly<BusyState> {
    return this.state;
  }

  isBusy(): boolean {
    return isBusyState(this.state);
  }

  registerButton(id: string, el: HTMLButtonElement, binding: BusyButtonBinding): void {
    this.bindings.set(id, { ...binding, el });
  }

  begin(key: BusyKey): void {
    if (this.state[key]) return;
    this.state = { ...this.state, [key]: true };
    this.syncDom();
  }

  end(key: BusyKey): void {
    if (!this.state[key]) return;
    this.state = { ...this.state, [key]: false };
    this.syncDom();
  }

  async run<T>(key: BusyKey, fn: () => Promise<T>): Promise<T> {
    this.begin(key);
    try {
      return await fn();
    } finally {
      this.end(key);
    }
  }

  isShowingBusyLabel(id: string): boolean {
    const binding = this.bindings.get(id);
    if (!binding) return false;
    return this.state[binding.busyKey];
  }

  isButtonDisabledByBusy(id: string): boolean {
    const binding = this.bindings.get(id);
    if (!binding) return false;
    if (this.state[binding.busyKey]) return true;
    if (binding.blockDuringCandidateMutation && this.shouldDisableCandidateActions()) {
      return true;
    }
    return false;
  }

  /** Hint for buttons not registered with BusyUiController (e.g. dynamic insert providers). */
  cursorHintForExternalDisabled(disabled: boolean): CursorHint | null {
    return resolveDisabledHint(disabled, false, this.isBusy());
  }

  shouldDisableCandidateActions(): boolean {
    return (
      this.state.evaluating
      || this.state.approving
      || this.state.rejecting
      || this.state.loadingDiff
    );
  }

  private syncDom(): void {
    const busy = isBusyState(this.state);
    this.ariaRoot.setAttribute("aria-busy", busy ? "true" : "false");

    if (busy) {
      if (this.busyTimer === undefined) {
        this.busyTimer = setTimeout(() => {
          this.doc.body.classList.add("is-busy");
        }, BUSY_CURSOR_DELAY_MS);
      }
    } else {
      if (this.busyTimer !== undefined) {
        clearTimeout(this.busyTimer);
        this.busyTimer = undefined;
      }
      this.doc.body.classList.remove("is-busy");
    }

    for (const [id, binding] of this.bindings) {
      const showBusyLabel = this.isShowingBusyLabel(id);
      binding.el.textContent = showBusyLabel ? binding.busyLabel : binding.idleLabel;
      const busyBlock = this.isButtonDisabledByBusy(id);
      if (busyBlock) {
        binding.el.disabled = true;
        applyCursorHint(binding.el, "busy");
      } else {
        binding.el.disabled = false;
        applyCursorHint(binding.el, null);
      }
    }

    this.onStateChange?.(this.state);
  }

  /** Re-apply disabled state from business rules after busy labels are set. */
  applyExternalDisabled(id: string, disabled: boolean): void {
    const binding = this.bindings.get(id);
    if (!binding) return;
    const busyBlock = this.isButtonDisabledByBusy(id);
    const isDisabled = busyBlock || disabled;
    binding.el.disabled = isDisabled;
    applyCursorHint(
      binding.el,
      resolveDisabledHint(disabled, busyBlock, this.isBusy()),
    );
    if (!this.isShowingBusyLabel(id)) {
      binding.el.textContent = binding.idleLabel;
    }
  }
}
