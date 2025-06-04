const StateManager = {
  state: {
    user: { name: "", age: "" },
  },

  updateUserField(field, value) {
    this.state.user[field] = value;
    EventBus.publish(`user.${field}Changed`, value);
  },

  getUserData() {
    return this.state.user;
  }
};

const AppController = {
  init() {
    EventBus.subscribe("user.nameChanged", this.handleUserUpdate);
    EventBus.subscribe("user.ageChanged", this.handleUserUpdate);
    EventBus.subscribe("viewRequested", this.handleViewChange);
  },

  handleUserUpdate(value) {
    console.log("Benutzerdaten aktualisiert:", value);
  },

  handleViewChange(viewName) {
    ViewManager.showView(viewName);
  }
};

const ViewManager = {
  views: {},

  registerView(name, viewObject) {
    this.views[name] = viewObject;
  },

  showView(name) {
    Object.values(this.views).forEach(view => view.hide());
    this.views[name]?.show();
  }
};

const HomeView = {
  element: document.getElementById("homeScreen"),
  userButton: document.getElementById("openUserForm"),

  init() {
    this.userButton.addEventListener("click", () => {
      EventBus.publish("viewRequested", "user");
    });
  },

  show() {
    this.element.style.display = "block";
  },

  hide() {
    this.element.style.display = "none";
  }
};

ViewManager.registerView("home", HomeView);
HomeView.init();

const UserView = {
  element: document.getElementById("userForm"),
  nameInput: document.getElementById("userName"),
  ageInput: document.getElementById("userAge"),
  saveButton: document.getElementById("saveUser"),

  init() {
    this.saveButton.addEventListener("click", () => {
      EventBus.publish("user.nameChanged", this.nameInput.value);
      EventBus.publish("user.ageChanged", this.ageInput.value);
    });

    EventBus.subscribe("user.nameChanged", this.updateName.bind(this));
    EventBus.subscribe("user.ageChanged", this.updateAge.bind(this));
  },

  updateName(name) {
    this.nameInput.value = name;
  },

  updateAge(age) {
    this.ageInput.value = age;
  },

  show() {
    this.element.style.display = "block";
  },

  hide() {
    this.element.style.display = "none";
  }
};

ViewManager.registerView("user", UserView);
UserView.init();
