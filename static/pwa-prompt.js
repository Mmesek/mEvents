class PWAPrompt {
    constructor(options = {}) {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.options = {
            position: options.position || 'bottom',
            autoDismiss: options.autoDismiss !== false,
            dismissDelay: options.dismissDelay || 7000,
            iconPath: options.iconPath || '/icon.png',
            ...options
        };

        this.init();
    }

    async init() {
        this.isInstalled = await this.checkInstallation();

        if (this.isInstalled) {
            return;
        }

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showPrompt();
        });

        window.addEventListener('appinstalled', () => {
            this.deferredPrompt = null;
            this.dismissPrompt();
        });
    }

    async checkInstallation() {
        if (window.navigator.standalone === true) {
            return true;
        }

        if (window.matchMedia('(display-mode: standalone)').matches) {
            return true;
        }

        return localStorage.getItem('pwa-installed') === 'true';
    }

    showPrompt() {
        const positionClasses = {
            bottom: 'bottom-6 left-6 right-6 sm:left-auto sm:right-6 sm:max-w-sm',
            top: 'top-6 left-6 right-6 sm:left-auto sm:right-6 sm:max-w-sm',
            corner: 'bottom-6 right-6 w-80'
        };

        const prompt = document.createElement('div');
        prompt.id = 'pwa-prompt';
        prompt.className = `fixed z-50 ${positionClasses[this.options.position]} animate-in fade-in slide-in-from-bottom-4 duration-300`;
        prompt.innerHTML = `
      <div class="uk-card rounded-lg shadow-lg p-4">
        <div class="flex gap-4 items-start">
          <!-- Icon -->
          <div class="flex-shrink-0">
            <img src="${this.options.iconPath}" alt="App icon" class="w-10 h-10 object-contain" />
          </div>
          
          <!-- Text Content -->
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-semibold text-white-900">Dodaj jako aplikację</h3>
            <p class="text-sm text-white-600 mt-1">i otwieraj z ekranu głównego</p>
          </div>
          
          <!-- Actions -->
          <div class="grid gap-2 flex-shrink-0">
            <button id="pwa-install" class="uk-btn uk-btn-primary" type="button">
                Dodaj
            </button>
            <button id="pwa-dismiss" class="uk-btn uk-btn-secondary" type="button">
              Nie.
            </button>
          </div>
        </div>
      </div>
    `;

        document.body.appendChild(prompt);

        document.getElementById('pwa-install').addEventListener('click', () => this.install());
        document.getElementById('pwa-dismiss').addEventListener('click', () => this.dismissPrompt());

        if (this.options.autoDismiss) {
            setTimeout(() => this.dismissPrompt(), this.options.dismissDelay);
        }
    }

    async install() {
        if (!this.deferredPrompt) return;

        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;

        if (outcome === 'accepted') {
            localStorage.setItem('pwa-installed', 'true');
        }

        this.dismissPrompt();
    }

    dismissPrompt() {
        const prompt = document.getElementById('pwa-prompt');
        if (prompt) {
            prompt.classList.add('animate-out', 'fade-out', 'slide-out-to-bottom-4', 'duration-200');
            setTimeout(() => prompt.remove(), 200);
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new PWAPrompt({
        position: 'bottom',
        autoDismiss: true,
        dismissDelay: 5000,
        iconPath: '/static/icons/favicon.svg'
    });
});