package com.panda.order_producer.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.panda.order_producer.model.OrderCreated;
import com.panda.order_producer.service.OrderProducer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/orders")
@Slf4j
@RequiredArgsConstructor
public class OrderController {

    private final OrderProducer orderProducer;

    @PostMapping
    public ResponseEntity<Map<String, String>> createOrder( @RequestBody OrderCreated orderRequest) {
        log.debug("Request order create received");

        try {
            // Generate order ID and timestamp
            String orderId = "ORD-" + UUID.randomUUID().toString().toUpperCase();
            Long timestamp = System.currentTimeMillis();

            OrderCreated order = OrderCreated.builder()
                    .orderId(orderId)
                    .customerId(orderRequest.getCustomerId())
                    .items(orderRequest.getItems())
                    .price(orderRequest.getPrice())
                    .timestamp(timestamp)
                    .build();

            orderProducer.sendOrderCreatedEvent(order);

            return ResponseEntity.status(HttpStatus.CREATED)
                    .body(Map.of(
                            "message", "Order created successfully",
                            "order_id", orderId
                    ));

        } catch (JsonProcessingException ex) {
            log.error("Failed to serialize order", ex);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "Failed to process order"));
        }
    }
}
