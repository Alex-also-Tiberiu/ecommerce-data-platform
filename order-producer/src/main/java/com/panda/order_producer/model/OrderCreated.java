package com.panda.order_producer.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class OrderCreated implements Serializable {

    @JsonProperty("order_id")
    private String orderId;

    @JsonProperty("customer_id")
    private String customerId;

    @JsonProperty("items")
    private List<Map<String, Object>> items;

    @JsonProperty("price")
    private Double price;

    @JsonProperty("timestamp")
    private Long timestamp;
}
