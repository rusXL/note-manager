DROP DATABASE IF EXISTS note_manager;

CREATE DATABASE IF NOT EXISTS note_manager;
USE note_manager;

-- ========== user ==========
CREATE TABLE IF NOT EXISTS user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL
);

-- ========== folder ==========
CREATE TABLE IF NOT EXISTS folder (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(50) NOT NULL,
    description TEXT,
    user_id INT NOT NULL,
    parent_folder_id INT,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (parent_folder_id) REFERENCES folder(id)
);

-- ========== note ==========
CREATE TABLE IF NOT EXISTS note (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    folder_id INT NOT NULL,
    FOREIGN KEY (folder_id) REFERENCES folder(id)
);

-- ========== TASK note (is-a subtype of note) ==========
CREATE TABLE IF NOT EXISTS task_note (
    note_id INT PRIMARY KEY,
    deadline DATE NOT NULL,
    priority INT NOT NULL,  -- 0=high, 1=mid, 2=low
    FOREIGN KEY (note_id) REFERENCES note(id)
);

-- ========== image ==========
CREATE TABLE IF NOT EXISTS image (
    note_id INT NOT NULL,
    url VARCHAR(255) NOT NULL,
    caption TEXT,
    PRIMARY KEY (note_id),
    FOREIGN KEY (note_id) REFERENCES note(id)
);
