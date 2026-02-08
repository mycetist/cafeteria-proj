/**
 * Student-specific JavaScript utilities
 * Handles student dashboard functionality and API calls
 */

/**
 * Load recent activity for the student dashboard
 * Fetches data from /api/dashboard endpoint which includes recent_meals
 */
async function loadRecentActivity() {
    const loadingEl = document.getElementById('activityLoading');
    const contentEl = document.getElementById('activityContent');
    const noActivityEl = document.getElementById('noActivity');
    const activityListEl = document.getElementById('activityList');
    
    try {
        const response = await Auth.apiCall('/api/dashboard');
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.recent_meals && data.recent_meals.length > 0) {
                activityListEl.innerHTML = data.recent_meals.map(meal => {
                    const date = new Date(meal.received_at).toLocaleDateString('ru-RU');
                    const time = new Date(meal.received_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                    const statusText = meal.is_confirmed ? 'Получен' : 'Ожидает';
                    return `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="mb-1">${meal.dish_name || 'Блюдо'}</h6>
                                    <small class="text-muted">${date} ${time}</small>
                                </div>
                                <span class="badge bg-success">${statusText}</span>
                            </div>
                        </li>
                    `;
                }).join('');
                
                loadingEl.classList.add('d-none');
                contentEl.classList.remove('d-none');
            } else {
                loadingEl.classList.add('d-none');
                noActivityEl.classList.remove('d-none');
            }
        } else {
            throw new Error('Failed to load activity');
        }
    } catch (error) {
        console.error('Error loading activity:', error);
        loadingEl.classList.add('d-none');
        noActivityEl.classList.remove('d-none');
    }
}

/**
 * Load dashboard data for students
 * Fetches subscription and balance information
 */
async function loadDashboardData() {
    try {
        const response = await Auth.apiCall('/api/subscription');
        if (response.ok) {
            const data = await response.json();
            if (data.subscription) {
                document.getElementById('subscriptionStatus').textContent = 'Активен';
                document.getElementById('mealsRemaining').textContent = data.subscription.meals_remaining;
            } else {
                document.getElementById('subscriptionStatus').textContent = 'Нет';
                document.getElementById('mealsRemaining').textContent = '-';
            }
        }
    } catch (error) {
        console.error('Error loading subscription:', error);
        document.getElementById('subscriptionStatus').textContent = 'Ошибка';
    }
}

/**
 * Load today's menu for students
 */
async function loadTodayMenu() {
    const loadingEl = document.getElementById('menuLoading');
    const contentEl = document.getElementById('menuContent');
    const noMenuEl = document.getElementById('noMenu');
    const menuItemsEl = document.getElementById('menuItems');
    
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await Auth.apiCall(`/api/menu/${today}`);
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.menu && data.menu.items && data.menu.items.length > 0) {
                document.getElementById('todayMenu').textContent = data.menu.items.length + ' блюд';
                
                menuItemsEl.innerHTML = data.menu.items.slice(0, 4).map(item => `
                    <div class="col-md-6 mb-2">
                        <div class="d-flex align-items-center p-2 border rounded">
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${item.dish.name}</h6>
                                <small class="text-muted">${item.dish.category}</small>
                            </div>
                            <span class="badge bg-primary">${item.dish.price} &#8381;</span>
                        </div>
                    </div>
                `).join('');
                
                loadingEl.classList.add('d-none');
                contentEl.classList.remove('d-none');
            } else {
                document.getElementById('todayMenu').textContent = 'Нет меню';
                loadingEl.classList.add('d-none');
                noMenuEl.classList.remove('d-none');
            }
        } else {
            throw new Error('Failed to load menu');
        }
    } catch (error) {
        console.error('Error loading menu:', error);
        loadingEl.classList.add('d-none');
        noMenuEl.classList.remove('d-none');
    }
}