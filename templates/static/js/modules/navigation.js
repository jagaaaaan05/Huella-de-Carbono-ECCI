// Screen and subtab navigation.

export const initNavigation = () => {
  const menuItems = document.querySelectorAll('.menu-item');
  const screens = document.querySelectorAll('.screen');
  const tabs = document.querySelectorAll('.tab[data-screen]');

  const setActiveMenuItem = (screenId) => {
    menuItems.forEach((item) => {
      item.classList.toggle('active', item.dataset.screen === screenId);
    });
  };

  const showScreen = (screenId) => {
    screens.forEach((s) => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) {
      target.classList.add('active');
    }
    setActiveMenuItem(screenId);
  };

  // Menu grid items
  menuItems.forEach((item) => {
    item.addEventListener('click', () => {
      const screenId = item.dataset.screen;
      showScreen(screenId);
      tabs.forEach((t) => t.classList.remove('active'));
      const currentTab = document.querySelector(`.tab[data-screen="${screenId}"]`);
      if (currentTab) {
        currentTab.classList.add('active');
      }
    });
  });

  // Top-level tab buttons
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const screenId = tab.dataset.screen;
      showScreen(screenId);
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
    });
  });

  setActiveMenuItem('screen-menu');

  // Subtab navigation within each screen
  document.querySelectorAll('.subtab').forEach((subtab) => {
    subtab.addEventListener('click', () => {
      const subId = subtab.dataset.sub;
      const parentSection = subtab.closest('.screen');
      parentSection.querySelectorAll('.subtab').forEach((btn) =>
        btn.classList.remove('active')
      );
      parentSection.querySelectorAll('.subscreen').forEach((sub) =>
        sub.classList.remove('active')
      );
      subtab.classList.add('active');
      const targetSub = parentSection.querySelector(`#sub-${subId}`);
      if (targetSub) {
        targetSub.classList.add('active');
      }
    });
  });
};
