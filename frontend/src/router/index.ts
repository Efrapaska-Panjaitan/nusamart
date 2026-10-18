import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import ProductListPage from '../pages/ProductListPage.vue'
import ProductDetailPage from '../pages/ProductDetailPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import RegisterPage from '../pages/RegisterPage.vue'
import CartPage from '../pages/CartPage.vue'
import CheckoutPage from '../pages/CheckoutPage.vue'
import OrdersPage from '../pages/OrdersPage.vue'
import ProfilePage from '../pages/ProfilePage.vue'
import WishlistPage from '../pages/WishlistPage.vue'
import AdminPage from '../pages/AdminPage.vue'
import NotFoundPage from '../pages/NotFoundPage.vue'
import { useAuthStore } from '../stores/auth'
const router = createRouter({ history: createWebHistory(), routes: [
  { path: '/', name: 'home', component: HomePage, meta: { title: 'Beranda' } },
  { path: '/products', name: 'products', component: ProductListPage, meta: { title: 'Katalog' } },
  { path: '/products/:slug', name: 'product-detail', component: ProductDetailPage, meta: { title: 'Detail Produk' } },
  { path: '/login', name: 'login', component: LoginPage, meta: { title: 'Masuk', guestOnly: true } },
  { path: '/register', name: 'register', component: RegisterPage, meta: { title: 'Daftar', guestOnly: true } },
  { path: '/cart', name: 'cart', component: CartPage, meta: { title: 'Keranjang', requiresAuth: true } },
  { path: '/checkout', name: 'checkout', component: CheckoutPage, meta: { title: 'Checkout', requiresAuth: true } },
  { path: '/orders', name: 'orders', component: OrdersPage, meta: { title: 'Pesanan', requiresAuth: true } },
  { path: '/profile', name: 'profile', component: ProfilePage, meta: { title: 'Profil', requiresAuth: true } },
  { path: '/wishlist', name: 'wishlist', component: WishlistPage, meta: { title: 'Wishlist', requiresAuth: true } },
  { path: '/admin', name: 'admin', component: AdminPage, meta: { title: 'Admin', requiresAuth: true, requiresAdmin: true } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundPage, meta: { title: 'Tidak Ditemukan' } },
], scrollBehavior: () => ({ top: 0 }) })
router.beforeEach(async to => {
  const auth = useAuthStore()
  if (auth.token && !auth.user) await auth.refreshMe()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.requiresAdmin && !auth.isAdmin) return { name: 'home' }
  if (to.meta.guestOnly && auth.isAuthenticated) return { name: 'home' }
  document.title = `${String(to.meta.title ?? 'NusaMart')} — NusaMart`
})
export default router
