package com.example;

import com.thoughtworks.xstream.annotations.XStreamImplicit;

import java.util.List;

public class AUser {

        public String id;

        public Integer index;

        public String guid;

        public Boolean isActive;

        public String balance;

        public String picture;

        public Integer age;

        public String eyeColor;

        public String name;

        public String gender;

        public String company;

        public String email;

        public String phone;

        public String address;

        public String about;

        public String registered;

        public Double latitude;

        public Double longitude;
        @XStreamImplicit(itemFieldName="tags")
        public List<String> tags = null;
        @XStreamImplicit(itemFieldName="friends")
        public List<Friend> friends = null;

        public String favoriteFruit;

    }

