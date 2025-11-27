<?php

class database
{
    private $host = "localhost";
    private $user = "root";
    private $pass = "";
    function __construct()
    {   
        return (new mysqli(
            $this->host,
            $this->user,
            $this->pass,
            'chatbot'
        ));
    }
}