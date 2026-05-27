<?php

/**
 * PlantAtHome AI Services Integration Examples for Laravel
 * Add these methods to your respective Laravel controllers or services.
 */

// 1. PLANT RECOMMENDATIONS
// In: App\Http\Controllers\RecommendationController

$response = Http::post(config('services.ai.recommendation_url') . '/recommendations', [
    'sunlight'          => $request->sunlight,       // 'low' | 'medium' | 'high'
    'room_type'         => $request->room_type,      // 'bedroom' | 'living_room' | etc.
    'budget'            => $request->budget,          // int (INR)
    'pet_friendly'      => $request->pet_friendly,   // bool
    'maintenance_level' => $request->maintenance,    // 'low' | 'medium' | 'high'
    'user_experience'   => $request->experience,     // 'beginner' | 'intermediate' | 'expert'
]);

$recommendations = $response->json('recommendations');


// 2. AI CHATBOT
// In: App\Http\Controllers\ChatController

$response = Http::post(config('services.ai.chatbot_url') . '/chat', [
    'message'    => $request->message,
    'session_id' => auth()->id() . '_' . session()->getId(),
    'language'   => app()->getLocale(),
]);

$reply = $response->json('reply');
$followUps = $response->json('follow_up_questions');


// 3. PLANT DOCTOR (with image upload to S3)
// In: App\Http\Controllers\PlantDoctorController

// Upload image to S3 via Laravel, then pass URL to plant doctor service
$imageUrl = Storage::disk('s3')->url($s3Path);

$response = Http::post(config('services.ai.plant_doctor_url') . '/plant-diagnosis', [
    'image_url'  => $imageUrl,
    'symptoms'   => $request->symptoms,
    'plant_name' => $request->plant_name,
]);

$diagnosis = $response->json();


// 4. SEO CONTENT GENERATION
// In: App\Console\Commands\GeneratePlantSeo or Admin Panel

$response = Http::post(config('services.ai.seo_url') . '/generate-content', [
    'plant_name' => $plant->name,
    'type'       => 'seo_description',     // 'seo_description' | 'blog_post' | 'meta_tags' | 'faq' | 'care_instructions'
    'keywords'   => ['indoor plant', 'buy plant online India', $plant->category],
    'tone'       => 'friendly',
]);

$content  = $response->json('content');
$metaTags = $response->json('meta_tags');

// Save to plant model
$plant->update([
    'seo_description' => $content,
    'meta_title'      => $metaTags['title'],
    'meta_description'=> $metaTags['description'],
]);


// 5. SEMANTIC SEARCH
// In: App\Http\Controllers\SearchController

$response = Http::post(config('services.ai.search_url') . '/search', [
    'query'   => $request->q,
    'top_k'   => 10,
    'filters' => [
        'max_price'   => $request->max_price,
        'pet_friendly'=> $request->pet_friendly,
    ],
]);

$results          = $response->json('results');
$interpretedQuery = $response->json('interpreted_query');


// 6. ADD TO SERVICES CONFIG (config/services.php)
// 'ai' => [
//     'recommendation_url' => env('RECOMMENDATION_SERVICE_URL', 'http://localhost:8001'),
//     'chatbot_url'        => env('CHATBOT_SERVICE_URL',        'http://localhost:8002'),
//     'plant_doctor_url'   => env('PLANT_DOCTOR_SERVICE_URL',   'http://localhost:8003'),
//     'seo_url'            => env('SEO_SERVICE_URL',            'http://localhost:8004'),
//     'search_url'         => env('SEMANTIC_SEARCH_SERVICE_URL','http://localhost:8005'),
// ],
