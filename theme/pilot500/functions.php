<?php
/**
 * Pilot500 theme setup.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'PILOT500_VERSION', '1.0.0' );

add_action( 'after_setup_theme', function () {
	add_theme_support( 'wp-block-styles' );
	add_theme_support( 'editor-styles' );
	add_editor_style( 'assets/css/site.css' );
} );

/* Front-end CSS and JS. The JS is small and has no dependencies. */
add_action( 'wp_enqueue_scripts', function () {
	wp_enqueue_style( 'pilot500', get_theme_file_uri( 'assets/css/site.css' ), array(), PILOT500_VERSION );
	wp_enqueue_script( 'pilot500', get_theme_file_uri( 'assets/js/site.js' ), array(), PILOT500_VERSION, array( 'in_footer' => true, 'strategy' => 'defer' ) );
} );

/* Mark JS as available before first paint, so reveal animations never flash. */
add_action( 'wp_head', function () {
	echo "<script>document.documentElement.classList.add('p5-js')</script>\n";
}, 1 );

add_filter( 'body_class', function ( $classes ) {
	$classes[] = 'p5';
	return $classes;
} );

/* Pattern category: every section lives under Patterns > Pilot500. */
add_action( 'init', function () {
	register_block_pattern_category( 'pilot500', array( 'label' => __( 'Pilot500', 'pilot500' ) ) );
} );
