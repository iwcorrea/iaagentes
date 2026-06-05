export const SITE_CONFIG = {
  name: "CampoDirecto",
  tagline: "Del campo a tu mesa",
  description: "Conectamos productores campesinos con consumidores urbanos",
  email: "hola@campodirecto.co",
  phone: "+57 1 234 5678",
  address: "Calle 10 # 5-67, Bogotá, Colombia",
  social: {
    facebook: "https://facebook.com/campodirecto",
    instagram: "https://instagram.com/campodirecto",
    twitter: "https://twitter.com/campodirecto",
    whatsapp: "https://wa.me/5712345678",
  },
};

export const NAV_LINKS = [
  { label: "Inicio", href: "/" },
  { label: "Productos", href: "/productos" },
  { label: "Categorías", href: "/categorias" },
  { label: "Productores", href: "/productores" },
  { label: "Nosotros", href: "/nosotros" },
  { label: "Contacto", href: "/contacto" },
];

export const PRODUCT_CATEGORIES = [
  {
    id: "frutas",
    name: "Frutas Frescas",
    slug: "frutas",
    description: "Frutas de temporada cultivadas con amor",
    image: "/images/categories/frutas.jpg",
    count: 124,
  },
  {
    id: "verduras",
    name: "Verduras y Hortalizas",
    slug: "verduras",
    description: "Verduras frescas directamente del huerto",
    image: "/images/categories/verduras.jpg",
    count: 98,
  },
  {
    id: "lacteos",
    name: "Lácteos y Quesos",
    slug: "lacteos",
    description: "Productos lácteos artesanales",
    image: "/images/categories/lacteos.jpg",
    count: 56,
  },
  {
    id: "carnes",
    name: "Carnes y Embutidos",
    slug: "carnes",
    description: "Carnes de crianza libre y natural",
    image: "/images/categories/carnes.jpg",
    count: 43,
  },
  {
    id: "hortalizas",
    name: "Hortalizas",
    slug: "hortalizas",
    description: "Hortalizas orgánicas certificadas",
    image: "/images/categories/hortalizas.jpg",
    count: 72,
  },
  {
    id: "granos",
    name: "Granos y Semillas",
    slug: "granos",
    description: "Granos tradicionales y superfoods",
    image: "/images/categories/granos.jpg",
    count: 38,
  },
];

export const REGIONS = [
  { id: "cundinamarca", name: "Cundinamarca" },
  { id: "boyaca", name: "Boyacá" },
  { id: "antioquia", name: "Antioquia" },
  { id: "santander", name: "Santander" },
  { id: "nariño", name: "Nariño" },
  { id: "cauca", name: "Cauca" },
];

export const SORT_OPTIONS = [
  { label: "Más recientes", value: "newest" },
  { label: "Precio: menor a mayor", value: "price-asc" },
  { label: "Precio: mayor a menor", value: "price-desc" },
  { label: "Más populares", value: "popular" },
  { label: "Mejor calificados", value: "rating" },
];
