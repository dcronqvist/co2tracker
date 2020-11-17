# Global Supply Chain CO2 Tracker 🌱
A four week project at Chalmers University in collaboration with Ericsson in the Course Sustainable development and ethics for computer science.

## Vision 💡
The idea is to design a system that enables sustainable purchasing decisions by being able to track CO2 emissions throughout the supply chain. This will make it easier for consumers and producers to make more informed decisions regarding their purchases and visualize their impact in a growing circular economy.

We envision a system that calculates the accumulated amount of CO2 emissions by looking at two components, namely processes and transport. These affect the accumulated CO2 value of an end product. If you visualize this as a tree, you can imagine the nodes as products and the edges as either transport or a process. Where process is a change from one product to another, eg a raw material used to manufacture a new product. This enables a large tracking opportunity by following a product's path through the tree, however, this relies on reliable standards for product identification.

In practice, we want to structure a database that holds information about different processes and transports and how much CO2 they emit. Furthermore, we will create an API to communicate with this database - which enables producers and carriers to continuously update the amount of CO2 emissions made per process / mode of transport. In the database, we imagine that a process should depend on other processes, which will create this tree-like structure, from the end product at the top, and the basic raw materials at the bottom.

##Course 
ENM156 - Sustainable development and ethics for computer science
https://student.portal.chalmers.se/en/chalmersstudies/courseinformation/pages/searchcourse.aspx?course_id=28619&parsergrp=3
