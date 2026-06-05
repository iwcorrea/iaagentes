export type UserRole = "comprador" | "vendedor" | "admin";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
  phone?: string;
  createdAt: string;
}

export interface Product {
  id: string;
  sellerId: string;
  sellerName: string;
  categoryId: string;
  categoryName: string;
  name: string;
  slug: string;
  description: string;
  price: number;
  originalPrice?: number;
  unit: string;
  stock: number;
  images: string[];
  isOrganic: boolean;
  isSeasonal: boolean;
  origin: string;
  region: string;
  rating: number;
  reviewCount: number;
  certifications: string[];
  createdAt: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string;
  image: string;
  count: number;
  parentId?: string;
}

export interface CartItem {
  id: string;
  productId: string;
  product: Product;
  quantity: number;
}

export interface Order {
  id: string;
  userId: string;
  items: OrderItem[];
  status: OrderStatus;
  total: number;
  subtotal: number;
  shipping: number;
  discount: number;
  shippingAddress: Address;
  paymentMethod: string;
  createdAt: string;
  updatedAt: string;
}

export interface OrderItem {
  id: string;
  productId: string;
  productName: string;
  productImage: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "refunded";

export interface Address {
  id: string;
  name: string;
  street: string;
  number: string;
  complement?: string;
  neighborhood: string;
  city: string;
  department: string;
  zipCode: string;
  phone: string;
  isDefault: boolean;
}

export interface Review {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  productId: string;
  rating: number;
  comment: string;
  createdAt: string;
}

export interface Producer {
  id: string;
  userId: string;
  storeName: string;
  description: string;
  avatar?: string;
  coverImage?: string;
  certifications: string[];
  location: string;
  region: string;
  latitude: number;
  longitude: number;
  rating: number;
  productCount: number;
  joinedAt: string;
  schedule?: string;
  contactPhone?: string;
}

export interface Testimonial {
  id: string;
  name: string;
  role: string;
  avatar?: string;
  content: string;
  rating: number;
}

export interface Notification {
  id: string;
  type: "order" | "message" | "review" | "system" | "promotion";
  title: string;
  message: string;
  read: boolean;
  link?: string;
  createdAt: string;
}

export interface SearchFilters {
  query?: string;
  category?: string;
  region?: string;
  minPrice?: number;
  maxPrice?: number;
  isOrganic?: boolean;
  isSeasonal?: boolean;
  certification?: string;
  sort?: string;
  page?: number;
  limit?: number;
}
