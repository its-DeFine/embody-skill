/* global window */
(function attachEmbodyDataChannelClient(globalScope) {
  function resolvePixelStreaming(scope) {
    return scope.pixelStreaming || scope.PixelStreaming || null;
  }

  function getVideoState(scope) {
    return Array.from(scope.document.querySelectorAll("video")).map((video) => {
      const trackCount =
        video.srcObject && typeof video.srcObject.getTracks === "function"
          ? video.srcObject.getTracks().length
          : 0;
      return {
        readyState: video.readyState,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        currentTime: video.currentTime,
        paused: video.paused,
        trackCount,
      };
    });
  }

  class EmbodyDataChannelClient {
    constructor(pixelStreaming, scope) {
      if (!pixelStreaming) {
        throw new Error("Pixel Streaming instance unavailable");
      }
      this.pixelStreaming = pixelStreaming;
      this.scope = scope;
    }

    static getPixelStreaming(scope = globalScope) {
      return resolvePixelStreaming(scope);
    }

    static async waitForPixelStreaming(options = {}) {
      const scope = options.scope || globalScope;
      const timeoutMs = options.timeoutMs || 15000;
      const pollMs = options.pollMs || 100;
      const startedAt = Date.now();

      while (Date.now() - startedAt < timeoutMs) {
        const pixelStreaming = resolvePixelStreaming(scope);
        if (pixelStreaming) {
          return new EmbodyDataChannelClient(pixelStreaming, scope);
        }
        await new Promise((resolve) => scope.setTimeout(resolve, pollMs));
      }

      throw new Error("Timed out waiting for Pixel Streaming");
    }

    async waitForPlayableVideo(options = {}) {
      const timeoutMs = options.timeoutMs || 20000;
      const pollMs = options.pollMs || 100;
      const startedAt = Date.now();

      while (Date.now() - startedAt < timeoutMs) {
        const videos = getVideoState(this.scope);
        const playable = videos.some((video) => {
          return (
            (video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0) ||
            video.trackCount > 0
          );
        });
        if (playable) {
          return videos;
        }
        await new Promise((resolve) => this.scope.setTimeout(resolve, pollMs));
      }

      throw new Error("Timed out waiting for playable video");
    }

    getState() {
      return {
        methods: Object.getOwnPropertyNames(Object.getPrototypeOf(this.pixelStreaming)),
        videos: getVideoState(this.scope),
        href: this.scope.location.href,
      };
    }

    addResponseListener(listener) {
      if (typeof this.pixelStreaming.addResponseEventListener !== "function") {
        throw new Error("Pixel Streaming response listener API unavailable");
      }
      this.pixelStreaming.addResponseEventListener(listener);
    }

    removeResponseListener(listener) {
      if (typeof this.pixelStreaming.removeResponseEventListener !== "function") {
        return;
      }
      this.pixelStreaming.removeResponseEventListener(listener);
    }

    sendCommand(command) {
      if (!command || typeof command !== "string") {
        throw new Error("Command string required");
      }
      if (typeof this.pixelStreaming.emitCommand !== "function") {
        throw new Error("emitCommand unavailable");
      }
      this.pixelStreaming.emitCommand({ command });
      return { ok: true, command };
    }

    sendCommands(commands, options = {}) {
      const delayMs = options.delayMs || 0;
      const sent = [];
      const queue = Array.isArray(commands) ? commands : [];
      const run = async () => {
        for (const command of queue) {
          sent.push(this.sendCommand(command));
          if (delayMs > 0) {
            await new Promise((resolve) => this.scope.setTimeout(resolve, delayMs));
          }
        }
        return sent;
      };
      return run();
    }
  }

  globalScope.EmbodyDataChannelClient = EmbodyDataChannelClient;
})(window);
