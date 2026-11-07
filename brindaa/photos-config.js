/**
 * ====================================================================
 * BRINDA'S ADVANCE BIRTHDAY SURPRISE - CENTRALIZED PHOTO CONFIGURATION
 * ====================================================================
 * 
 * You can easily add, remove, reorder, or edit captions for Brinda's photos here.
 * 
 * To add a new photo:
 * 1. Place the image file in the project folder (or in 'assets/images/').
 * 2. Add an entry to the `BRINDA_PHOTOS` array below.
 * 3. Save this file — the website will automatically load and display it!
 * 
 * Fields explained:
 * - id: Unique identifier
 * - src: Path to the image file
 * - fallbackSrc: Backup path in case of alternate file location
 * - title: Short title for the photo
 * - caption: Beautiful handwritten-style caption
 * - story: Optional longer heartfelt memory/note for the photo viewer
 * - tag: Sweet tag (e.g., 'Radiant Smile', 'Pure Elegance')
 * - date: Date or memory label
 * - featured: Set to true if featured on the hero / reveal screen
 */

const BRINDA_PHOTOS = [
  {
    id: "brinda-portrait",
    src: "assets/images/brinda-portrait.jpeg",
    fallbackSrc: "vb.jpeg",
    title: "The Birthday Queen 👑",
    caption: "That radiant smile that lights up every room ✨",
    story: "Brinda in her stunning pink and lavender elegance. A smile that makes every ordinary day feel extraordinary.",
    tag: "Queen Vibes",
    date: "A Day to Remember",
    featured: true
  },
  {
    id: "brinda-smile",
    src: "assets/images/brinda-smile.jpeg",
    fallbackSrc: "WhatsApp Image 2026-11-06 at 10.09.43 P.jpeg",
    title: "Sunshine Over Her Shoulder ☀️",
    caption: "Looking back with that signature effortless grace 💖",
    story: "Caught in between laughter and candid magic. Always spreading warmth, joy, and positive energy wherever she goes.",
    tag: "Pure Sunshine",
    date: "Golden Moments",
    featured: false
  },
  {
    id: "brinda-grace",
    src: "assets/images/brinda-grace.jpeg",
    fallbackSrc: "WhatsApp Image 2026-11-06 at 10.09.43 PM.jpeg",
    title: "Elegance in Every Step 🌸",
    caption: "Sunlight, smiles, and the best friend anyone could ask for 🌿",
    story: "Standing tall, graceful, and glowing in the afternoon shade. Every moment shared with you is a cherished memory.",
    tag: "Grace & Charm",
    date: "Cherished Times",
    featured: false
  }
];

const BRINDA_VIDEO = {
  id: "brinda-super-surprise",
  src: "assets/video/brinda-super-surprise.mp4",
  fallbackSrc: "assets/video/WhatsApp Video 2026-11-06 at 10.20.27 PM.mp4",
  poster: "assets/images/video-poster.jpg",
  title: "Brinda's Super Surprise Video 🎬✨",
  caption: "A special cinematic video edit made just for you 💖"
};

window.BRINDA_VIDEO = BRINDA_VIDEO;

// Helper functions for easy access across components
window.BRINDA_PHOTO_STORE = {
  photos: BRINDA_PHOTOS,
  video: BRINDA_VIDEO,
  getAll: function() {
    return this.photos;
  },
  getVideo: function() {
    return this.video;
  },
  getById: function(id) {
    return this.photos.find(p => p.id === id) || this.photos[0];
  },
  getFeatured: function() {
    return this.photos.filter(p => p.featured) || [this.photos[0]];
  }
};

