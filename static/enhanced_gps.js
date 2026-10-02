// ENHANCED GPS TRACKER FOR WEB APP
// This provides Android-like GPS accuracy in browser

class EnhancedGPSTracker {
    constructor() {
        this.watchId = null;
        this.bestLocation = null;
        this.locationHistory = [];
        this.isTracking = false;
    }

    // Start continuous GPS tracking (like Android)
    startTracking(callback, errorCallback) {
        if (!navigator.geolocation) {
            errorCallback('Geolocation not supported');
            return;
        }

        this.isTracking = true;
        this.bestLocation = null;
        this.locationHistory = [];

        // ULTRA HIGH ACCURACY - Similar to Android GPS_PROVIDER
        const options = {
            enableHighAccuracy: true,  // Force GPS hardware
            timeout: 60000,            // 60 seconds timeout
            maximumAge: 0              // No cached data
        };

        // Use watchPosition for continuous updates (like Android)
        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                this.processLocation(position, callback);
            },
            (error) => {
                errorCallback(this.getErrorMessage(error));
            },
            options
        );

        console.log('📡 GPS Tracking started (continuous mode)');
    }

    // Process incoming location and filter for best accuracy
    processLocation(position, callback) {
        const location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp,
            altitude: position.coords.altitude,
            speed: position.coords.speed,
            heading: position.coords.heading
        };

        // Add to history
        this.locationHistory.push(location);

        // Keep only last 10 readings
        if (this.locationHistory.length > 10) {
            this.locationHistory.shift();
        }

        // Update best location if this is more accurate
        if (!this.bestLocation || location.accuracy < this.bestLocation.accuracy) {
            this.bestLocation = location;
            console.log(`📍 New best accuracy: ${location.accuracy.toFixed(2)}m`);
        }

        // Quality check
        const quality = this.getLocationQuality(location.accuracy);
        
        callback({
            ...location,
            quality: quality,
            isBest: location === this.bestLocation,
            historicalAverage: this.getAverageAccuracy()
        });
    }

    // Get average accuracy from history
    getAverageAccuracy() {
        if (this.locationHistory.length === 0) return 0;
        const sum = this.locationHistory.reduce((acc, loc) => acc + loc.accuracy, 0);
        return sum / this.locationHistory.length;
    }

    // Get smoothed location (average of recent readings)
    getSmoothedLocation() {
        if (this.locationHistory.length === 0) return null;

        // Use last 5 readings for smoothing
        const recent = this.locationHistory.slice(-5);
        
        const avgLat = recent.reduce((sum, loc) => sum + loc.latitude, 0) / recent.length;
        const avgLng = recent.reduce((sum, loc) => sum + loc.longitude, 0) / recent.length;
        const avgAcc = recent.reduce((sum, loc) => sum + loc.accuracy, 0) / recent.length;

        return {
            latitude: avgLat,
            longitude: avgLng,
            accuracy: avgAcc,
            isSmoothed: true
        };
    }

    // Stop tracking
    stopTracking() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
            this.isTracking = false;
            console.log('📡 GPS Tracking stopped');
        }
    }

    // Get location quality rating
    getLocationQuality(accuracy) {
        if (accuracy <= 10) return { level: 'perfect', emoji: '🎯', color: '#10b981' };
        if (accuracy <= 50) return { level: 'excellent', emoji: '✅', color: '#22c55e' };
        if (accuracy <= 100) return { level: 'good', emoji: '👍', color: '#84cc16' };
        if (accuracy <= 500) return { level: 'moderate', emoji: '⚠️', color: '#f59e0b' };
        if (accuracy <= 1000) return { level: 'poor', emoji: '❌', color: '#ef4444' };
        return { level: 'very poor', emoji: '🚫', color: '#dc2626' };
    }

    // Get error message
    getErrorMessage(error) {
        switch(error.code) {
            case error.PERMISSION_DENIED:
                return 'Location permission denied. Please enable location access.';
            case error.POSITION_UNAVAILABLE:
                return 'Location unavailable. Please ensure GPS is enabled.';
            case error.TIMEOUT:
                return 'Location request timed out. Please try again.';
            default:
                return 'Unknown error occurred.';
        }
    }

    // Get single high-accuracy location (with retry)
    async getSingleLocation(maxRetries = 3) {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            let bestResult = null;

            const tryGetLocation = () => {
                attempts++;
                console.log(`📡 GPS attempt ${attempts}/${maxRetries}`);

                const options = {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                };

                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const accuracy = position.coords.accuracy;
                        
                        // Store if this is the best so far
                        if (!bestResult || accuracy < bestResult.coords.accuracy) {
                            bestResult = position;
                        }

                        // Accept if accuracy is good enough
                        if (accuracy <= 100) {
                            console.log(`✅ Good accuracy achieved: ${accuracy.toFixed(2)}m`);
                            resolve(bestResult);
                        } else if (attempts < maxRetries) {
                            console.log(`⚠️ Accuracy ${accuracy.toFixed(2)}m, retrying...`);
                            setTimeout(tryGetLocation, 2000); // Wait 2s before retry
                        } else {
                            console.log(`⚠️ Max retries reached. Best: ${bestResult.coords.accuracy.toFixed(2)}m`);
                            resolve(bestResult);
                        }
                    },
                    (error) => {
                        if (attempts < maxRetries) {
                            console.log(`❌ Error, retrying... (${attempts}/${maxRetries})`);
                            setTimeout(tryGetLocation, 2000);
                        } else {
                            reject(this.getErrorMessage(error));
                        }
                    },
                    options
                );
            };

            tryGetLocation();
        });
    }
}

// Export for use
window.EnhancedGPSTracker = EnhancedGPSTracker;

