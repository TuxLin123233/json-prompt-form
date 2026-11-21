const CACHE = "jpf-v6";
const CORE = [
  "./",
  "index.html",
  "builder.html",
  "checker.html",
  "manifest.webmanifest",
  "assets/icon-192.png",
  "assets/icon-512.png",
  "assets/banner.svg",
  "assets/illustrations/hero.svg",
  "assets/illustrations/step-copy.svg",
  "assets/illustrations/step-save.svg",
  "assets/illustrations/step-resume.svg",
  "assets/illustrations/feature.svg",
  "assets/illustrations/empty.svg",
  "form.json",
  "schema.json",
  "updates.json",
  "examples/study-exam.json",
  "examples/fitness.json",
  "examples/job-search.json",
  "examples/emotion-support.json",
  "examples/finance.json",
  "examples/writing.json",
  "examples/sleep.json",
  "examples/quit-habits.json",
  "examples/language-learning.json",
  "examples/parenting.json",
  "examples/caregiver.json",
  "examples/adhd.json",
  "examples/reading.json",
  "examples/pet.json",
  "examples/time-management.json",
  "examples/morning-routine.json",
  "examples/meditation.json",
  "examples/healthy-diet.json",
  "examples/journaling.json",
  "examples/public-speaking.json",
  "examples/relationship.json",
  "examples/declutter.json",
  "examples/instrument.json",
  "examples/coding.json",
  "examples/cooking.json",
  "examples/plant-care.json",
  "examples/project.json"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(CORE.map(url => new Request(url, { cache: "reload" }))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req, { cache: "no-store" })
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(cache => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then(hit => hit || caches.match("index.html")))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req, { cache: "no-cache" }).then(res => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(cache => cache.put(req, copy));
        }
        return res;
      });
    })
  );
});
