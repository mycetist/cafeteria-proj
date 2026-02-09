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
                    const statusClass = meal.is_confirmed ? 'success' : 'warning';
                    return `
                        <li class="activity-item">
                            <div class="activity-icon ${statusClass}">
                                <i class="bi ${meal.is_confirmed ? 'bi-check-lg' : 'bi-clock'}"></i>
                            </div>
                            <div class="activity-content">
                                <div class="activity-title">${meal.dish_name || 'Блюдо'}</div>
                                <div class="activity-time">${date} ${time} · ${statusText}</div>
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
    
    // Load wallet balance
    try {
        console.log('Loading wallet balance...');
        const walletResponse = await Auth.apiCall('/api/wallet');
        console.log('Wallet API response status:', walletResponse.status);
        
        if (walletResponse.ok) {
            const walletData = await walletResponse.json();
            console.log('Wallet data:', walletData);
            const balance = walletData.wallet ? walletData.wallet.balance : 0;
            console.log('Parsed balance:', balance);
            document.getElementById('balance').textContent = balance.toFixed(2) + ' ₽';
        } else {
            console.error('Wallet API failed with status:', walletResponse.status);
            const errorText = await walletResponse.text();
            console.error('Error response:', errorText);
            document.getElementById('balance').textContent = '0.00 ₽';
        }
    } catch (error) {
        console.error('Error loading wallet:', error);
        document.getElementById('balance').textContent = '0.00 ₽';
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
                
                menuItemsEl.innerHTML = data.menu.items.map(item => `
                    <div class="menu-item-card">
                        <div class="menu-item-info">
                            <div class="menu-item-name">${item.dish.name}</div>
                            <div class="menu-item-type">${item.dish.category}</div>
                        </div>
                        <div class="menu-item-price">${item.dish.price} &#8381;</div>
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