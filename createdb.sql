CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(35) UNIQUE NOT NULL,
    first_name VARCHAR(30),
    last_name VARCHAR(30)
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand VARCHAR(30),
    description_ TEXT,
    img VARCHAR(255),
    title VARCHAR(255),
    product_type VARCHAR(100),
    rating FLOAT(4, 3),
    reviews INT,
    url VARCHAR(255)
);

CREATE TABLE product_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code BIT(3) NOT NULL,
    title VARCHAR(30) NOT NULL
);

CREATE TABLE product_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    availability VARCHAR(100) NOT NULL,
    title VARCHAR(30) NOT NULL,
    price INT NOT NULL,
    product_id INT NOT NULL,
    product_changes_id INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (product_changes_id) REFERENCES product_changes(id)
);

CREATE TABLE monitoring_list (
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, product_id)
);

INSERT INTO product_changes (code, title)
VALUES
    (b'000', "No changes"),
    (b'001', "Price"),
    (b'010', "Option"),
    (b'011', "Price & Option"),
    (b'100', "Availability"),
    (b'101', "Availability & Price"),
    (b'110', "Availability & Option"),
    (b'111', "All");