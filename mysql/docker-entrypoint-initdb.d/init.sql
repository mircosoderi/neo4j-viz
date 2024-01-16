CREATE TABLE Dot (
    id INT not null,
    label VARCHAR(255),
    x INT,
    y INT,
    radius INT,
	color VARCHAR(255),
	deleted BOOLEAN,
	timestamp BIGINT,
	PRIMARY KEY (id)
);

CREATE TABLE marked_for_deletion (
	id int not null, 
	PRIMARY KEY (id)
);